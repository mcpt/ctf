import uuid
import time
import kubernetes
from django.conf import settings

if settings.CHALLENGE_CLUSTER['connection']['host'] is not None:
    cluster_config = kubernetes.client.Configuration()
    cluster_config.host = settings.CHALLENGE_CLUSTER['connection']['host']
    cluster_config.api_key = {'authorization': 'Bearer {}'.format(settings.CHALLENGE_CLUSTER['connection']['token'])}
    cluster_config.ssl_ca_cert = settings.CHALLENGE_CLUSTER['connection']['caCert']
    api_client = kubernetes.dynamic.DynamicClient(kubernetes.client.ApiClient(cluster_config))

def create_challenge_instance(challenge_spec, problem_id, problem_flag, instance_owner, wait=False):
    def generate_identifier():
        return uuid.uuid4().hex[-7:]

    instance_id = generate_identifier()
    instance_name = f'{problem_id}-{instance_id}'

    existing_challenge_instance = fetch_challenge_instance(challenge_spec, problem_id, instance_owner)
    if existing_challenge_instance is not None:
        return None

    job_v1 = api_client.resources.get(api_version='batch/v1', kind='Job')
    service_v1 = api_client.resources.get(api_version='v1', kind='Service')
    ingress_v1 = api_client.resources.get(api_version='networking.k8s.io/v1', kind='Ingress')

    labels = {
        'ctf-problem': problem_id,
        'ctf-instance': instance_id,
        'ctf-instance-owner': instance_owner,
        'app.kubernetes.io/component': 'challenge',
        'app.kubernetes.io/managed-by': 'mCTF',
    }

    job_manifest = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {
            'name': instance_name,
            'labels': labels,
            'annotations': {
                f'container.apparmor.security.beta.kubernetes.io/{container["name"]}': ('unconfined' if container['apparmor']['type'] == 'Unconfined' else f'localhost/{container["apparmor"]["localhostProfile"]}' if container['apparmor']['type'] == 'Localhost' else 'runtime/default')
            for container in challenge_spec['containers'] if 'apparmorProfile' in container},
        },
        'spec': {
            'backoffLimit': 4,
            'activeDeadlineSeconds': challenge_spec['duration'],
            'ttlSecondsAfterFinished': 0,
            'template': {
                'metadata': {
                    'labels': labels,
                },
                'spec': {
                    'containers': [{
                        'name': container['name'],
                        'image': container['image']['imageRef'],
                        'imagePullPolicy': 'IfNotPresent',
                        'ports': [{
                            'name': port['name'],
                            'containerPort': port['port'],
                        } for port in container['ports']],
                    }
                        | ({'env': [(env, {'name': 'FLAG', 'value': problem_flag})[env['name'] == 'FLAG'] for env in container['env']]} if 'env' in container else {})
                        | ({'resources': container['resources']} if 'resources' in container else {})
                        | ({'livenessProbe': container['livenessProbe']} if 'livenessProbe' in container else {})
                        | ({'securityContext': {k: v for k, v in settings.CHALLENGE_CLUSTER['securityContexts'][container['securityContext']].items() if k != 'apparmorProfile'}} if 'securityContext' in container else {})
                    for container in challenge_spec['containers']],
                    'imagePullSecrets': [{'name': settings.CHALLENGE_CLUSTER['imagePullSecrets'][container['image']['imagePullSecret']]} for container in challenge_spec['containers'] if 'imagePullSecret' in container['image']],
                    'autoMountServiceAccountToken': False,
                    'restartPolicy': 'OnFailure',
                }
                    | ({'runtimeClassName': settings.CHALLENGE_CLUSTER['runtimeClassNames'][challenge_spec["runtimeClassName"]]} if 'runtimeClassName' in challenge_spec else {})
            },
        },
    }

    job = job_v1.create(body=job_manifest, namespace=settings.CHALLENGE_CLUSTER['namespace'])

    ports_expose = []
    for container in challenge_spec['containers']:
        ports_expose.extend([port for port in container['ports'] if 'expose' in port and port['expose']])

    for i in range(len(ports_expose)):
        ports_expose[i] |= {'svcPort': 20000 + i}

    nodeport_ports = []
    ingress_ports = []
    for port in ports_expose:
        if port['protocol'] == 'HTTP':
            ingress_ports.append(port | {'host': settings.CHALLENGE_CLUSTER["domain"].format(generate_identifier())})
        else:
            nodeport_ports.append(port | {'host': settings.CHALLENGE_CLUSTER["domain"].format(instance_id)})

    def create_service(svc_type, ports):
        service_manifest = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f'{instance_name}-{"http" if svc_type == "ClusterIP" else "tcp"}',
                'labels': labels,
                'ownerReferences': [{
                    'apiVersion': 'batch/v1',
                    'kind': 'Job',
                    'name': job.metadata.name,
                    'uid': job.metadata.uid,
                }],
            },
            'spec': {
                'type': svc_type,
                'selector': {
                    'ctf-instance': instance_id,
                },
                'ports': [{
                    'name': port['name'],
                    'protocol': 'TCP' if port['protocol'] == 'HTTP' else port['protocol'],
                    'port': port['svcPort'],
                    'targetPort': port['port'],
                } for port in ports],
            },
        }

        return service_v1.create(body=service_manifest, namespace=settings.CHALLENGE_CLUSTER['namespace'])

    if len(nodeport_ports) > 0:
        nodeport_svc = create_service('NodePort', nodeport_ports)

    if len(ingress_ports) > 0:
        clusterip_svc = create_service('ClusterIP', ingress_ports)

        ingress_manifest = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': instance_name,
                'labels': labels,
                'ownerReferences': [{
                    'apiVersion': 'v1',
                    'kind': 'Service',
                    'name': clusterip_svc.metadata.name,
                    'uid': clusterip_svc.metadata.uid,
                }],
            },
            'spec': {
                'rules': [{
                    'host': port['host'],
                    'http': {
                        'paths': [{
                            'pathType': 'Prefix',
                            'path': '/',
                            'backend': {
                                'service': {
                                    'name': clusterip_svc.metadata.name,
                                    'port': {
                                        'number': port['svcPort'],
                                    },
                                },
                            },
                        }],
                    },
                } for port in ingress_ports],
            },
        }

        ingress = ingress_v1.create(body=ingress_manifest, namespace=settings.CHALLENGE_CLUSTER['namespace'])

    if wait:
        pod_v1 = api_client.resources.get(api_version='v1', kind='Pod')
        while True:
            time.sleep(1)
            pod_list = pod_v1.get(namespace=settings.CHALLENGE_CLUSTER['namespace'], label_selector=f'ctf-instance={instance_id}').items
            if len(pod_list) > 0 and pod_list[0].phase != 'Pending':
                break

    return fetch_challenge_instance(challenge_spec, problem_id=problem_id, instance_owner=instance_owner)

def fetch_challenge_instance(challenge_spec, problem_id, instance_owner):
    job_v1 = api_client.resources.get(api_version='batch/v1', kind='Job')
    service_v1 = api_client.resources.get(api_version='v1', kind='Service')
    ingress_v1 = api_client.resources.get(api_version='networking.k8s.io/v1', kind='Ingress')

    job_list = job_v1.get(namespace=settings.CHALLENGE_CLUSTER['namespace'], label_selector=f'ctf-problem={problem_id},ctf-instance-owner={instance_owner}')

    if len(job_list.items) == 0:
        return None
    else:
        job = job_list.items[0]

        instance_name = job.metadata.name
        problem_id = job.metadata.labels['ctf-problem']
        instance_id = job.metadata.labels['ctf-instance']

    endpoints = []

    try:
        nodeport_svc = service_v1.get(namespace=settings.CHALLENGE_CLUSTER['namespace'], name=f'{job.metadata.name}-tcp')

        for port in nodeport_svc.spec.ports:
            endpoints.append({
                'name': port.name,
                'protocol': port.protocol,
                'host': settings.CHALLENGE_CLUSTER["domain"].format(instance_id),
                'port': port.nodePort,
            })
    except kubernetes.dynamic.exceptions.NotFoundError:
        pass

    try:
        clusterip_svc = service_v1.get(namespace=settings.CHALLENGE_CLUSTER['namespace'], name=f'{job.metadata.name}-http')
        ingress = ingress_v1.get(namespace=settings.CHALLENGE_CLUSTER['namespace'], name=job.metadata.name)

        clusterip_svc_port_name = {}
        for port in clusterip_svc.spec.ports:
            clusterip_svc_port_name[port.port] = port.name

        for rule in ingress.spec.rules:
            endpoints.append({
                'name': clusterip_svc_port_name[rule.http.paths[0].backend.service.port.number],
                'protocol': 'HTTP',
                'host': rule.host,
                'port': 80,
            })
    except kubernetes.dynamic.exceptions.NotFoundError:
        pass

    return {
        'instance': {
            'name': instance_name,
            'problem': problem_id,
            'id': instance_id,
        },
        'time': {
            'created_at': job.metadata.creationTimestamp,
            'duration': challenge_spec['duration'],
        },
        'endpoints': endpoints,
    }

def delete_challenge_instance(challenge_spec, problem_id, instance_owner):
    job_v1 = api_client.resources.get(api_version='batch/v1', kind='Job')

    challenge_instance_status = fetch_challenge_instance(challenge_spec, problem_id=problem_id, instance_owner=instance_owner)

    if challenge_instance_status is None:
        return

    job_v1.delete(namespace=settings.CHALLENGE_CLUSTER['namespace'], name=challenge_instance_status['instance']['name'], propagation_policy='Background')