const video = document.getElementById("camera");
const status = document.querySelector(".camera-status");

async function startCamera() {

    try {

        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        video.srcObject = stream;

        status.innerHTML = "🟢 Camera Connected";

    } catch (err) {

        status.innerHTML = "❌ Camera Permission Denied";
        console.log(err);

    }

}

startCamera();