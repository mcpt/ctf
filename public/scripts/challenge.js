let challengeTimerSetInterval;

function clearTimer() {
    if (challengeTimerSetInterval !== undefined) {
        window.clearInterval(challengeTimerSetInterval);
    }
}

function getCookie(name) {
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
    }
    return null;
}

async function getChallenge() {
    updateInterimStatus("Refreshing", " Status...", "chall__refresh");
    updateChallenge("GET", setLiveStatus, setNoneStatus);
}
async function createChallenge() {
    updateInterimStatus("Launching");
    updateChallenge("POST", setLiveStatus, getChallenge);
}
async function deleteChallenge() {
    updateInterimStatus("Deleting");
    updateChallenge("DELETE", setNoneStatus);
}

async function updateChallenge(method, handleSuccess, handleFailure) {
    if (handleFailure === undefined) handleFailure = handleSuccess;
    try {
        const json = await fetchChallenge(method);
        if (json) {
            handleSuccess(json)
        } else {
            handleFailure();
        }
    } catch (e) {
        toggleError();
    }
}
async function fetchChallenge(method) {
    return fetch(window.location + "/challenge", {
        "headers": {
            "X-CSRFToken": getCookie("csrftoken")
        },
        "method": method
    }).then(res => res.json());
}

function clearStatus() {
    const status_elm = document.getElementById("chall__status");
    const actions_elm = document.getElementById("chall__actions");

    while (status_elm.firstChild) status_elm.firstChild.remove();
    while (actions_elm.firstChild) actions_elm.firstChild.remove();
}

function displayTemplate(templateId, parentId, index = null) {
    const elem = document.getElementById(parentId);
    const content = document.getElementById(templateId).content.cloneNode(true);
    if (index !== null)
        elem.insertBefore(content, elem.childNodes[index]);
    else
        elem.appendChild(content);
}

function setNoneStatus() {
    clearTimer();
    clearStatus();

    displayTemplate("chall-none", "chall__status");
    displayTemplate("chall__action__create", "chall__actions");
    displayTemplate("chall__action__refresh", "chall__actions");
}

function setLiveStatus(json) {
    clearTimer();
    clearStatus();

    displayTemplate("chall-live", "chall__status");

    const endpt_list = document.getElementById("chall__endpoints");
    for (let endpt of json.endpoints) {
        let li = document.createElement("li");
        let conn = document.createElement("code");

        conn.textContent = endpt.connection;

        li.appendChild(conn);
        endpt_list.appendChild(li);
    }

    if (json.instance.owner !== "everyone") {
        displayTemplate("chall__delete", "chall__status");
        displayTemplate("chall__action__delete", "chall__actions");
    }
    displayTemplate("chall__action__refresh", "chall__actions");

    // Count down the instance expiry
    function displayTime() {
        countdownTimer(new Date(new Date(json.time.created_at).getTime() + json.time.duration * 1000), "chall__expiry", setNoneStatus, "this moment", "");
    }

    displayTime();
    challengeTimerSetInterval = setInterval(displayTime, 1000);
}

function updateInterimStatus(verbing, suffix = " Instance...", elemId = "chall__verb") {
    toggleError(false);
    try {
        const btn = document.getElementById(elemId);

        btn.textContent = verbing + suffix;
        displayTemplate("chall__action_button_spinner", elemId, index = 0);

        btn.disabled = true;
    } catch (e) { }
}
function toggleError(show = true) {
    document.getElementById("chall__error").textContent = show ? "An error has occured. Please try again later." : "";
}

getChallenge();
