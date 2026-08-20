window.onload = function () {

    const question = document.getElementById("questionText").innerText;
    const status = document.getElementById("aiStatus");

    function speakQuestion() {

        status.innerHTML = "🗣 Speaking...";

        speechSynthesis.cancel();

        const speech = new SpeechSynthesisUtterance(question);

        speech.lang = "en-US";
        speech.rate = 0.95;
        speech.pitch = 1;
        speech.volume = 1;

        speech.onend = function () {
            status.innerHTML = "🎤 Waiting for your answer...";
        };

        speechSynthesis.speak(speech);
    }

    // Speak automatically when page loads
    speakQuestion();

    // Replay button
    document.getElementById("speakQuestion").addEventListener("click", function () {
        speakQuestion();
    });

};
// ===============================
// Speech to Text
// ===============================

const micBtn = document.getElementById("micBtn");
const answerBox = document.getElementById("answer");

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    micBtn.addEventListener("click", function () {

        recognition.start();

        micBtn.innerHTML = "🎙 Listening...";
        document.getElementById("aiStatus").innerHTML = "🎤 Listening...";

    });

    recognition.onresult = function(event) {

        const transcript = event.results[0][0].transcript;

        answerBox.value += transcript + " ";

    };

    recognition.onend = function() {

        micBtn.innerHTML = "🎤 Speak";
        document.getElementById("aiStatus").innerHTML = "✅ Speech Captured";

    };

    recognition.onerror = function(event){

        micBtn.innerHTML = "🎤 Speak";
        document.getElementById("aiStatus").innerHTML = "❌ " + event.error;

    };

} else {

    micBtn.disabled = true;
    micBtn.innerHTML = "Speech Not Supported";

}