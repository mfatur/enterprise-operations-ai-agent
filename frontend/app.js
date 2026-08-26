const API_BASE_URL = "";

const questionInput =
    document.getElementById(
        "questionInput"
    );


const sendButton =
    document.getElementById(
        "sendButton"
    );


const chatMessages =
    document.getElementById(
        "chatMessages"
    );


const revenueValue =
    document.getElementById(
        "revenueValue"
    );


const quantityValue =
    document.getElementById(
        "quantityValue"
    );


const averageOrderValue =
    document.getElementById(
        "averageOrderValue"
    );
let topProductsChart = null;
let revenueByRegionChart = null;

/* =========================
   FORMAT RUPIAH
========================= */

function formatRupiah(value) {

    return new Intl.NumberFormat(
        "id-ID",
        {
            style: "currency",
            currency: "IDR",
            maximumFractionDigits: 0
        }
    ).format(value);

}


/* =========================
   CHAT MESSAGE
========================= */

function addMessage(
    message,
    sender
) {

    const messageWrapper =
        document.createElement(
            "div"
        );


    messageWrapper.className =
        `message ${sender}`;


    const content =
        document.createElement(
            "div"
        );


    content.className =
        "message-content";


    content.textContent =
    message.replace(
        /\*\*(.*?)\*\*/g,
        "$1"
    );

messageWrapper.appendChild(
    content
);

chatMessages.appendChild(
    messageWrapper
);

chatMessages.scrollTop =
    chatMessages.scrollHeight;
}


/* =========================
   SEND QUESTION
========================= */

async function sendQuestion() {

    const question =
        questionInput.value.trim();


    if (!question) {
        return;
    }


    if (question.length < 3) {

        addMessage(
            "Pertanyaan minimal 3 karakter.",
            "assistant"
        );

        return;
    }


    addMessage(
        question,
        "user"
    );


    questionInput.value = "";


    sendButton.disabled = true;

    sendButton.textContent =
        "Mengirim...";


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question: question
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Terjadi kesalahan."
            );
        }


        addMessage(
            data.answer,
            "assistant"
        );


    } catch (error) {

        console.error(
            "Chat error:",
            error
        );


        addMessage(
            `Terjadi kesalahan: ${error.message}`,
            "assistant"
        );


    } finally {

        sendButton.disabled = false;

        sendButton.textContent =
            "Kirim";
    }
}


/* =========================
   TOP PRODUCTS
========================= */

function renderTopProducts(products) {

    const container =
        document.getElementById(
            "topProducts"
        );

    const canvas =
        document.getElementById(
            "topProductsChart"
        );


    container.innerHTML = "";


    if (
        !products ||
        products.length === 0
    ) {

        container.innerHTML =
            `<div class="empty-state">
                Tidak ada data.
            </div>`;

        return;
    }


    if (topProductsChart) {

        topProductsChart.destroy();

    }


    const labels =
        products.map(
            (item) => item.product
        );


    const values =
        products.map(
            (item) => item.total_quantity
        );


    const barCtx = canvas.getContext("2d");
    const barGradient = barCtx.createLinearGradient(0, 0, 0, 260);
    barGradient.addColorStop(0, "#2563EB");
    barGradient.addColorStop(1, "#2563EB");

    Chart.defaults.font.family = "'Inter', sans-serif";

    topProductsChart =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {
                    labels: labels,

                    datasets: [
                        {
                            label: "Units Sold",

                            data: values,

                            backgroundColor: barGradient,

                            borderRadius: 6,

                            maxBarThickness: 64,

                            borderWidth: 0
                        }
                    ]
                },

                options: {
                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: false
                        }
                    },

                    scales: {
                        y: {
                            beginAtZero: true,

                            grid: {
                                color: "#EEF0F5"
                            },

                            ticks: {
                                precision: 0,
                                color: "#6B7080"
                            }
                        },

                        x: {
                            grid: {
                                display: false
                            },

                            ticks: {
                                color: "#12141C"
                            }
                        }
                    }
                }
            }
        );


    products.forEach(
        (item) => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "analytics-item";


            const name =
                document.createElement(
                    "span"
                );


            name.className =
                "analytics-name";


            name.textContent =
                item.product;


            const value =
                document.createElement(
                    "span"
                );


            value.className =
                "analytics-value";


            value.textContent =
                `${item.total_quantity} unit`;


            row.appendChild(name);

            row.appendChild(value);

            container.appendChild(row);

        }
    );
}

/* =========================
   REVENUE BY REGION
========================= */

function renderRevenueByRegion(regions) {

    const container =
        document.getElementById(
            "revenueByRegion"
        );

    const canvas =
        document.getElementById(
            "revenueByRegionChart"
        );


    container.innerHTML = "";


    if (
        !regions ||
        regions.length === 0
    ) {

        container.innerHTML =
            `<div class="empty-state">
                Tidak ada data.
            </div>`;

        return;
    }


    if (revenueByRegionChart) {

        revenueByRegionChart.destroy();

    }


    const labels =
        regions.map(
            (item) => item.region
        );


    const values =
        regions.map(
            (item) => item.revenue
        );


    const regionCtx = canvas.getContext("2d");
    const regionGradient = regionCtx.createLinearGradient(0, 0, 260, 0);
    regionGradient.addColorStop(0, "#2563EB");
    regionGradient.addColorStop(1, "#2563EB");

    Chart.defaults.font.family = "'Inter', sans-serif";

    revenueByRegionChart =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {
                    labels: labels,

                    datasets: [
                        {
                            label: "Revenue",

                            data: values,

                            backgroundColor: regionGradient,

                            borderRadius: 6,

                            maxBarThickness: 32,

                            borderWidth: 0
                        }
                    ]
                },

                options: {
                    indexAxis: "y",

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: false
                        },

                        tooltip: {
                            callbacks: {
                                label:
                                    function(context) {

                                        return formatRupiah(
                                            context.raw
                                        );

                                    }
                            }
                        }
                    },

                    scales: {
                        x: {
                            beginAtZero: true,

                            grid: {
                                color: "#EEF0F5"
                            },

                            ticks: {
                                color: "#6B7080",
                                callback:
                                    function(value) {

                                        return formatRupiah(
                                            value
                                        );

                                    }
                            }
                        },

                        y: {
                            grid: {
                                display: false
                            },

                            ticks: {
                                color: "#12141C"
                            }
                        }
                    }
                }
            }
        );


    regions.forEach(
        (item) => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "analytics-item";


            const name =
                document.createElement(
                    "span"
                );


            name.className =
                "analytics-name";


            name.textContent =
                item.region;


            const value =
                document.createElement(
                    "span"
                );


            value.className =
                "analytics-value";


            value.textContent =
                formatRupiah(
                    item.revenue
                );


            row.appendChild(name);

            row.appendChild(value);

            container.appendChild(row);

        }
    );
}

/* =========================
   LOAD DASHBOARD
========================= */

async function loadDashboard() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/dashboard`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Gagal mengambil data dashboard."
            );
        }


        revenueValue.textContent =
            formatRupiah(
                data.total_revenue
            );


        quantityValue.textContent =
            `${data.total_quantity_sold} unit`;


        averageOrderValue.textContent =
            formatRupiah(
                data.average_order_value
            );


        renderTopProducts(
            data.top_products
        );


        renderRevenueByRegion(
            data.revenue_by_region
        );


    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );


        revenueValue.textContent =
            "Error";


        quantityValue.textContent =
            "Error";


        averageOrderValue.textContent =
            "Error";
    }
}


/* =========================
   SUGGESTED QUESTIONS
========================= */

const suggestionButtons =
    document.querySelectorAll(
        ".suggestion-btn"
    );


suggestionButtons.forEach(
    (button) => {

        button.addEventListener(
            "click",
            () => {

                questionInput.value =
                    button.textContent.trim();


                sendQuestion();

            }
        );

    }
);


/* =========================
   EVENT HANDLERS
========================= */

sendButton.addEventListener(
    "click",
    sendQuestion
);


questionInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter"
        ) {

            sendQuestion();

        }

    }
);


/* =========================
   INITIAL LOAD
========================= */

loadDashboard();