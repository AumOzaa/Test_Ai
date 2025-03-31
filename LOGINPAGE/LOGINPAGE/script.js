document.addEventListener("DOMContentLoaded", () => {
    const auth = firebase.auth();
    let isProcessing = false;

    // Form switching functions
    function showForm(formToShow) {
        document.querySelectorAll(".form-box").forEach(form => {
            form.classList.add("hidden");
        });
        formToShow.classList.remove("hidden");
    }

    // Form switching event listeners
    document.getElementById("signUpLink").addEventListener("click", (e) => {
        e.preventDefault();
        showForm(document.getElementById("signUpForm"));
    });

    document.getElementById("backToSignIn").addEventListener("click", (e) => {
        e.preventDefault();
        showForm(document.getElementById("signInForm"));
    });

    document.getElementById("forgotPasswordLink").addEventListener("click", (e) => {
        e.preventDefault();
        showForm(document.getElementById("forgotPasswordForm"));
    });

    document.getElementById("backToSignIn2").addEventListener("click", (e) => {
        e.preventDefault();
        showForm(document.getElementById("signInForm"));
    });

    // Sign In Function
    document.getElementById("signInBtn").addEventListener("click", async (e) => {
        e.preventDefault();
        if (isProcessing) return;
        
        isProcessing = true;
        const email = document.getElementById("signInEmail").value;
        const password = document.getElementById("signInPassword").value;
        const errorElement = document.getElementById("signInError");
        errorElement.textContent = "";

        try {
            await auth.signInWithEmailAndPassword(email, password);
            // The auth state listener will handle redirect
        } catch (error) {
            errorElement.textContent = error.message;
            isProcessing = false;
        }
    });

    // Sign Up Function
    document.getElementById("signUpBtn").addEventListener("click", async (e) => {
        e.preventDefault();
        if (isProcessing) return;
        
        isProcessing = true;
        const email = document.getElementById("signUpEmail").value;
        const password = document.getElementById("signUpPassword").value;
        const errorElement = document.getElementById("signUpError");
        errorElement.textContent = "";

        try {
            await auth.createUserWithEmailAndPassword(email, password);
            showForm(document.getElementById("signInForm"));
        } catch (error) {
            errorElement.textContent = error.message;
        }
        isProcessing = false;
    });

    // Password Reset Function
    document.getElementById("resetPasswordBtn").addEventListener("click", async (e) => {
        e.preventDefault();
        if (isProcessing) return;
        
        isProcessing = true;
        const email = document.getElementById("forgotPasswordEmail").value;
        const errorElement = document.getElementById("resetError");
        errorElement.textContent = "";

        try {
            await auth.sendPasswordResetEmail(email);
            errorElement.textContent = "Password reset email sent!";
            showForm(document.getElementById("signInForm"));
        } catch (error) {
            errorElement.textContent = error.message;
        }
        isProcessing = false;
    });
});