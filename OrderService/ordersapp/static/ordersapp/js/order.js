document.addEventListener("DOMContentLoaded", () => {
    const selects = document.querySelectorAll(".form-floating select");

    selects.forEach(select => {
        // Add or remove 'has-value' class based on current value
        const update = () => {
            if (select.value) {
                select.classList.add("has-value");
            } else {
                select.classList.remove("has-value");
            }
        };

        select.addEventListener("change", update);
        update(); // initialize
    });
});
