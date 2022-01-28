function countdownTimer(dateObj, elemId, expiry_msg="Time's up!", suffix=" left") {
    const difference = +dateObj - +new Date();
    let remaining = expiry_msg;

    if (difference > 0) {
        const parts = {
            days: Math.floor(difference / (1000 * 60 * 60 * 24)),
            hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
            minutes: Math.floor((difference / 1000 / 60) % 60),
            seconds: Math.floor((difference / 1000) % 60),
        };
        remaining = Object.keys(parts).map(part => {
            return `${parts[part]} ${part}`;
        }).join(" ");
        remaining += suffix;
    } else {
        location.reload(true);
    }

    document.getElementById(elemId).textContent = remaining;
}
