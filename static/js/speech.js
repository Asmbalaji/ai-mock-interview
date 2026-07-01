const micBtn = document.getElementById("micBtn");
const answerBox = document.getElementById("answer");

const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {

    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    micBtn.addEventListener("click", () => {
        recognition.start();

        micBtn.innerHTML = "🎙 Listening...";
        micBtn.disabled = true;
    });

    recognition.onresult = function(event) {

        let transcript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }

        answerBox.value = transcript;
    };

    recognition.onend = function() {

        micBtn.innerHTML = "🎤 Speak";
        micBtn.disabled = false;

    };

} else {

    micBtn.style.display = "none";
    alert("Speech Recognition is not supported in this browser.");

}