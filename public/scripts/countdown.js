function countdownTimer(dateObj, elemId, expiryAction = () => { }, expiryMsg = "Time's up!", suffix = " left") {
    const difference = +dateObj - +new Date();
    let remaining = expiryMsg;

    if (difference >= 1000) {
        const parts = {
            day: Math.floor(difference / (1000 * 60 * 60 * 24)),
            hour: Math.floor((difference / (1000 * 60 * 60)) % 24),
            minute: Math.floor((difference / 1000 / 60) % 60),
            second: Math.floor((difference / 1000) % 60),
        };
        let partSum = 0;
        remaining = Object.keys(parts).filter(part => {
            partSum += parts[part];
            return partSum > 0;
        }).map(part => {
            return `${parts[part]} ${part}${parts[part] != 1 ? 's' : ''}`;
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
