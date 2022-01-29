function countdownTimer(dateObj, elemId, expiryAction = () => { }, expiryMsg = "Time's up!", suffix = " left") {
    const difference = +dateObj - +new Date();
    let remaining = expiryMsg;

    if (difference >= 1000) {
        const parts = {
            days: Math.floor(difference / (1000 * 60 * 60 * 24)),
            hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
            minutes: Math.floor((difference / 1000 / 60) % 60),
            seconds: Math.floor((difference / 1000) % 60),
        };
        let partSum = 0;
        remaining = Object.keys(parts).filter(part => {
            partSum += parts[part];
            return partSum > 0;
        }).map(part => {
            return `${parts[part]} ${part}`;
        }).join(" ");
        remaining += suffix;
    } else if (difference < 0) {
        expiryAction();
    }

    const elem = document.getElementById(elemId)
    if (elem !== null) {
        elem.textContent = remaining;
    }
}
