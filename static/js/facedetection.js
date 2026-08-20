const videoElement = document.getElementById("camera");
const faceStatus = document.getElementById("faceStatus");

const faceDetection = new FaceDetection({
    locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`;
    }
});

faceDetection.setOptions({
    model: "short",
    minDetectionConfidence: 0.6
});

faceDetection.onResults((results) => {

    if(results.detections.length > 0){

        faceStatus.innerHTML="😊 Face Detected";
        faceStatus.style.color="green";

    }else{

        faceStatus.innerHTML="⚠ No Face Detected";
        faceStatus.style.color="red";

    }

});

const camera = new Camera(videoElement,{
    onFrame: async()=>{
        await faceDetection.send({image:videoElement});
    },
    width:640,
    height:480
});

camera.start();