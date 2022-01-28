async function getChallenge() {
    toggleError(false);
    try {
        const json = await fetchChallenge("GET");
        if (!json) {
            setNoneStatus();
        } else {
            setLiveStatus(json)
        }
    } catch (e) {
        toggleError();
    }
}

async function createChallenge() {
    toggleError(false);
    updateButtonStatus("Creating");

    try {
        const json = await fetchChallenge("POST");
        setLiveStatus(json)
    } catch (e) {
        toggleError();
    }
}
async function deleteChallenge() {
    toggleError(false);
    updateButtonStatus("Deleting");

    try {
        const json = await fetchChallenge("DELETE");
        setNoneStatus();
    } catch (e) {
        toggleError();
    }
}
async function fetchChallenge(method) {
    return fetch(window.location + "/challenge", {
        "headers": {
            "X-CSRFToken": document.cookie.split(";").find(i => i.split("=")[0]=== "csrftoken").split("=")[1]
        },
        "method": method
    }).then(res => res.json());
}

function setNoneStatus() {
    const status_elm = document.getElementById("chall__status");

    while (status_elm.firstChild) status_elm.firstChild.remove();

    status_elm.appendChild(document.getElementById(`chall-none`).content.cloneNode(true));
}
function setLiveStatus(json) {
    const status_elm = document.getElementById("chall__status");

    while (status_elm.firstChild) status_elm.firstChild.remove();

    status_elm.appendChild(document.getElementById(`chall-live`).content.cloneNode(true));

    const endpt_list = document.getElementById("chall__endpoints");
    for (let endpt of json.endpoints) {
        let li = document.createElement("li");
        let conn = document.createElement("code");

        conn.textContent = endpt.connection;

        li.appendChild(conn);
        endpt_list.appendChild(li);
    }
    status_elm.insertBefore(document.getElementById(`chall__delete`).content.cloneNode(true), document.getElementById("chall__error"))

    // Count down the instance expiry
    setInterval(countdownTimer, 1000, new Date(new Date(json.time.created_at) + json.time.duration * 1000), "chall__expiry", "this moment", "");
}

function updateButtonStatus(verbing, suffix=" instance...") {
    try {
        const btn = document.getElementById("chall__verb");
        btn.textContent = verbing + suffix;
        btn.disabled = true;
    } catch (e) {}
}
function toggleError(show=true) {
    document.getElementById("chall__error").textContent = show ? "An error has occured. Please try again later." : "";
}
