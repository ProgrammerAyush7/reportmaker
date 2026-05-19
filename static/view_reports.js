document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".share-btn").forEach(button => {

        button.addEventListener("click", async () => {

            const name = button.dataset.name;
            const id = button.dataset.id;

            const fileUrl = `/download-report/${id}`;

            try {

                // fetch actual pdf
                const response = await fetch(fileUrl);

                if (!response.ok) {
                    throw new Error("Failed to fetch PDF");
                }

                const blob = await response.blob();

                // create real file object
                const file = new File(
                    [blob],
                    `${name}${id}.pdf`,
                    {
                        type: "application/pdf"
                    }
                );

                // native mobile share
                if (
                    navigator.share &&
                    navigator.canShare &&
                    navigator.canShare({ files: [file] })
                ) {

                    await navigator.share({
                        title: `${name} Report`,
                        text: "Medical Report PDF",
                        files: [file]
                    });

                } else {

                    // fallback for unsupported devices
                    const a = document.createElement("a");

                    a.href = URL.createObjectURL(blob);
                    a.download = `${name}${id}.pdf`;

                    document.body.appendChild(a);

                    a.click();

                    a.remove();

                    URL.revokeObjectURL(a.href);
                }

            } catch (err) {

                console.error("Share failed:", err);

                // final fallback
                window.location.href = fileUrl;
            }
        });
    });
});