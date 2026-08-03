let timer = document.getElementById("timer");
let mainButton = document.getElementById("mainButton");
let resetButton = document.getElementById("resetButton");
let workTimeInput = document.getElementById("workTime");
let breakTimeInput = document.getElementById("breakTime");
let saveSettingsButton = document.getElementById("saveSettingsButton");
let sessionTitle = document.getElementById("sessionTitle");
let notification = document.getElementById("notification");
let notificationSound = new Audio("/static/sounds/notification.mp3");
let completedSessionsText = document.getElementById("completedSessions");
let totalFocusTimeText = document.getElementById("totalFocusTime");
let progressFill = document.getElementById("progressFill");
let progressText = document.getElementById("progressText");

let dailyGoal = 10;

let workMinutes = 25;
let breakMinutes = 5;

let completedSessions = 0;
let totalFocusTime = 0;

let minutes = workMinutes;
let seconds = 0;

let timerState = "idle";
let sessionType = "work";

let interval;

function updateProgress(){
    let percentage = (completedSessions/dailyGoal) * 100;
    progressFill.style.width = percentage + "%";
    progressText.innerText = completedSessions + " / " + dailyGoal + " Sessions (" + percentage + "%)";
};

function showNotification(message){
    notification.innerText = message;
    notification.style.display = "block";

    notificationSound.currentTime = 0;
    notificationSound.play();

    setTimeout(function(){
        notification.style.display = "none";
    }, 3000);
};

function updateTimerDisplay() {
    if (seconds < 10){
        timer.innerText = minutes + ":0" + seconds;
    }
    else{
        timer.innerText = minutes + ":" + seconds;
    }
};

function switchSessions() {
    if (sessionType === "work"){
        completedSessions++;
        totalFocusTime += workMinutes;
        updateProgress();
        completedSessionsText.innerText = completedSessions;
        totalFocusTimeText.innerText = totalFocusTime;
        showNotification("🍅 Work session complete!\nTime for a break ☕");
        sessionType = "break";
        minutes = breakMinutes;
        seconds = 0;
        sessionTitle.innerText = "☕ Break Time";
    }
            
    else{
        showNotification("☕ Break is over!\nLet's get back to work 🍅");
        sessionType = "work";
        minutes = workMinutes;
        seconds = 0;
        sessionTitle.innerText = "🍅 Work Session";
    }
};

function startTimer(){
    interval = setInterval(function(){
        if (minutes == 0 && seconds == 0){
            switchSessions();
            updateTimerDisplay();
            return;
        }
        else{
            seconds--;
        
            if (seconds < 0){
                minutes--;
                seconds = 59;
            }
        }
        
        updateTimerDisplay();
    }, 1000);
};

mainButton.addEventListener("click", function() {
    if (timerState === "idle"){
        timerState = "running";
        mainButton.innerText = "⏸ Pause";
        resetButton.style.display = "inline";
        startTimer();
    }

    else if (timerState === "running"){
        timerState = "paused";
        mainButton.innerText = "▶ Resume";
        resetButton.style.display = "inline";
        clearInterval(interval);
    }

    else if (timerState === "paused"){
        timerState = "running";
        mainButton.innerText = "⏸ Pause";
        resetButton.style.display = "inline";
        startTimer();
    }
});

resetButton.addEventListener("click", function() {
    clearInterval(interval);
    minutes = workMinutes;
    seconds = 0;
    updateTimerDisplay();
    timerState = "idle";
    mainButton.innerText = "▶ Start";
    resetButton.style.display = "none";
    sessionType = "work";
    sessionTitle.innerText = "🍅 Work Session"
});

saveSettingsButton.addEventListener("click", function(event){

    event.preventDefault();

    workMinutes = Number(workTimeInput.value);
    breakMinutes = Number(breakTimeInput.value);
    if (sessionType === 'work'){
        minutes = workMinutes;
    }
    else{
        minutes = breakMinutes;
    }
    
    seconds = 0;

    updateTimerDisplay();
});