document.addEventListener("DOMContentLoaded", () => {
    const selects = document.querySelectorAll(".form-floating select");

    // Highlight selects that have a value
    selects.forEach(select => {
        const update = () => {
            if (select.value) {
                select.classList.add("has-value");
            } else {
                select.classList.remove("has-value");
            }
        };

        select.addEventListener("change", update);
        update(); // Initial update on page load
    });

    // Auto-submit the form when any dropdown changes
    const form = document.getElementById("order-filters-form");
    if (form) {
        document.querySelectorAll("#order-filters-form select").forEach(select => {
            select.addEventListener("change", () => {
                form.submit();
            });
        });
    }
});
