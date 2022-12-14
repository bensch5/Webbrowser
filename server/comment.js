allow_submit = true;

label = document.querySelectorAll("label")[0];

function lengthCheck() {
    userInput = "" + this.getAttribute("value");
    allow_submit = (userInput.length <= 100);

    if (!allow_submit) {
        label.innerHTML = "Comment too long!";
    } else {
        label.innerHTML = "<div style=\"color:black\">All fine</div>";
    }

    if (userInput && userInput.charAt(userInput.length - 1) == '+') {
        label_like = document.querySelectorAll("label")[1];

        x = new XMLHttpRequest();
        x.open("POST", "likes", false);
        x.send("1");

        label_like.innerHTML = "<div>" + x.responseText + " likes so far" + "</div>";

        // Crash
        x = new XMLHttpRequest();
        x.open("GET", "https://www.google.com", false);
        console.log("HA!");
        x.send("888");
    }
}

input = document.querySelectorAll("input")[0];
input.addEventListener("keydown", lengthCheck);

form = document.querySelectorAll("form")[0];
form.addEventListener("submit", function(e) {
    if (!allow_submit) e.preventDefault();
});