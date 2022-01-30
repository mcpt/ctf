const participantSelect = document.querySelector('#id_participant');
const maxTeamSize = JSON.parse(document.getElementById('max-team-size').textContent);
const teamParticipantCount = JSON.parse(document.getElementById('team-participant-count').textContent);

if (maxTeamSize !== null && participantSelect !== null) {
    participantSelect.addEventListener('change', (event) => {
        const resultDisplay = document.querySelector('#team-size-display');

        if (event.target.value !== '') {
            const remainingSeats = maxTeamSize - teamParticipantCount[event.target.value];
            console.log(remainingSeats);
            resultDisplay.textContent = `${remainingSeats} seat${remainingSeats !== 1 ? 's' : ''} remaining on this team for this contest.`;
        } else {
            resultDisplay.textContent = '';
        }
    });
}