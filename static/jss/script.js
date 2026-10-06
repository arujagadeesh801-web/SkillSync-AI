/* =========================================
   STUDENT AI PLATFORM
   Global JavaScript
   ========================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =========================================
       FORM SUBMISSION HANDLING
       ========================================= */

    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            if (!form.checkValidity()) {
                return;
            }

            const submitButton = form.querySelector(
                'button[type="submit"], input[type="submit"]'
            );

            if (!submitButton) {
                return;
            }

            if (form.id === "predictionForm") {
                submitButton.textContent = "Analyzing...";
            }

            else if (form.id === "studyForm") {
                submitButton.textContent = "Thinking...";
            }

            else if (form.id === "resumeForm") {
                submitButton.textContent = "Analyzing Resume...";
            }

            else if (form.id === "quizForm") {
                submitButton.textContent = "Submitting...";
            }

            else {
                submitButton.textContent = "Please wait...";
            }

            submitButton.disabled = true;
        });

    });


    /* =========================================
       RESUME FILE INPUT
       ========================================= */

    const resumeInput = document.getElementById("resume");

    const fileNameDisplay =
        document.getElementById("fileName");

    if (resumeInput) {

        resumeInput.addEventListener("change", function () {

            if (!fileNameDisplay) {
                return;
            }

            if (resumeInput.files.length > 0) {

                const file = resumeInput.files[0];

                fileNameDisplay.textContent =
                    file.name;

            } else {

                fileNameDisplay.textContent =
                    "No file selected";

            }

        });

    }


    /* =========================================
       RESUME DRAG AND DROP
       ========================================= */

    const uploadArea =
        document.querySelector(".upload-area");

    if (uploadArea && resumeInput) {

        uploadArea.addEventListener(
            "dragover",
            function (event) {

                event.preventDefault();

                uploadArea.classList.add("dragover");

            }
        );


        uploadArea.addEventListener(
            "dragleave",
            function () {

                uploadArea.classList.remove("dragover");

            }
        );


        uploadArea.addEventListener(
            "drop",
            function (event) {

                event.preventDefault();

                uploadArea.classList.remove("dragover");

                const files =
                    event.dataTransfer.files;

                if (files.length > 0) {

                    resumeInput.files = files;

                    if (fileNameDisplay) {

                        fileNameDisplay.textContent =
                            files[0].name;

                    }

                }

            }
        );

    }


    /* =========================================
       STUDY ASSISTANT SUGGESTED QUESTIONS
       ========================================= */

    const suggestionButtons =
        document.querySelectorAll(".suggestion-btn");

    const questionInput =
        document.querySelector(
            'input[name="question"], textarea[name="question"]'
        );

    suggestionButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            if (!questionInput) {
                return;
            }

            const question =
                button.dataset.question ||
                button.textContent.trim();

            questionInput.value = question;

            questionInput.focus();

        });

    });


    /* =========================================
       AUTO HIDE SUCCESS / ERROR MESSAGES
       ========================================= */

    const messages =
        document.querySelectorAll(
            ".success-message, .error-message"
        );

    messages.forEach(function (message) {

        setTimeout(function () {

            message.style.transition =
                "opacity 0.3s ease";

            message.style.opacity = "0";

            setTimeout(function () {

                if (message.parentNode) {
                    message.remove();
                }

            }, 300);

        }, 5000);

    });


    /* =========================================
       NUMBER INPUT VALIDATION
       ========================================= */

    const numberInputs =
        document.querySelectorAll(
            'input[type="number"]'
        );

    numberInputs.forEach(function (input) {

        input.addEventListener("input", function () {

            if (input.value === "") {
                return;
            }

            const value =
                parseFloat(input.value);

            const min =
                input.min !== ""
                    ? parseFloat(input.min)
                    : null;

            const max =
                input.max !== ""
                    ? parseFloat(input.max)
                    : null;


            if (min !== null && value < min) {
                input.value = min;
            }

            if (max !== null && value > max) {
                input.value = max;
            }

        });

    });


    /* =========================================
       PREVENT DOUBLE FORM SUBMISSION
       ========================================= */

    forms.forEach(function (form) {

        let submitted = false;

        form.addEventListener(
            "submit",
            function (event) {

                if (submitted) {

                    event.preventDefault();

                    return;
                }

                if (form.checkValidity()) {

                    submitted = true;

                }

            }
        );

    });


    /* =========================================
       MOBILE NAVIGATION
       ========================================= */

    const menuButton =
        document.querySelector(".menu-toggle");

    const navigation =
        document.querySelector(".nav-links");

    if (menuButton && navigation) {

        menuButton.addEventListener(
            "click",
            function () {

                navigation.classList.toggle(
                    "active"
                );

            }
        );

    }


    /* =========================================
       CONFIRM LOGOUT
       ========================================= */

    const logoutLinks =
        document.querySelectorAll(
            'a[href="/logout"]'
        );

    logoutLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const confirmed =
                    confirm(
                        "Are you sure you want to logout?"
                    );

                if (!confirmed) {

                    event.preventDefault();

                }

            }
        );

    });


    /* =========================================
       BUTTON LOADING STATE
       ========================================= */

    const loadingButtons =
        document.querySelectorAll(
            "[data-loading-text]"
        );

    loadingButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const loadingText =
                    button.dataset.loadingText;

                if (loadingText) {

                    button.textContent =
                        loadingText;

                    button.disabled = true;

                }

            }
        );

    });

});