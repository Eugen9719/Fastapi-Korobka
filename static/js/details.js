import {BASE_URL} from './config.js';
import {getUser} from "./base.js";

document.addEventListener("DOMContentLoaded", async function () {
    const selectedDateElement = document.querySelector(".selected-date");
    const prevButton = document.querySelector(".prev-day");
    const nextButton = document.querySelector(".next-day");

    const stadiumId = document.getElementById("stadium-id").innerText;
    const timeSlots = document.querySelectorAll(".time-slot");

    let currentDate = new Date();


    const months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ];


    function updateDateDisplay() {
        let day = currentDate.getDate();
        let month = months[currentDate.getMonth()];
        selectedDateElement.textContent = `${day} ${month}`;
        fetchBookings(); // Загружаем бронирования при изменении даты
    }

    prevButton.addEventListener("click", function () {
        currentDate.setDate(currentDate.getDate() - 1);
        updateDateDisplay();
    });

    nextButton.addEventListener("click", function () {
        currentDate.setDate(currentDate.getDate() + 1);
        updateDateDisplay();
    });

    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
    }

    async function fetchBookings() {
        console.log("Date:", `${currentDate}`);
        try {
            const response = await fetch(`${BASE_URL}/booking/booking_from_date?stadium_id=${stadiumId}&date=${formatDate(currentDate)}`);
            const bookings = await response.json();
            await markBookedSlots(bookings);
        } catch (error) {
            console.error("Ошибка при загрузке бронирований: ", error);
        }
    }

    async function markBookedSlots(bookings) {
        const user = await getUser();
        if (!user) return;

        const allSlots = document.querySelectorAll('.time-slot');
        allSlots.forEach(slot => slot.classList.remove('booked', 'my-booking'));

        bookings.forEach(booking => {
            const startTime = booking.start_time.substring(11, 16);
            const endTime = booking.end_time.substring(11, 16);

            let currentTime = startTime;
            while (currentTime < endTime) {
                const nextTime = add30Minutes(currentTime);
                const slot = document.querySelector(`.time-slot[data-time="${currentTime}-${nextTime}"]`);
                console.log("Slot for time:", `${currentTime}-${nextTime}`);

                if (slot) {
                    if (booking.user_id === user.id) { // ✅ Исправлено: берем ID пользователя из booking
                        slot.classList.add("my-booking");
                    } else {
                        slot.classList.add("booked"); // Чужая бронь
                    }
                } else {
                    console.error("Slot not found for time:", `${currentTime}-${nextTime}`);
                }
                currentTime = nextTime;
            }
        });
    }


    function add30Minutes(time) {
        const [hours, minutes] = time.split(':').map(Number);
        let newMinutes = minutes + 30;
        let newHours = hours;
        if (newMinutes >= 60) {
            newMinutes -= 60;
            newHours += 1;
        }
        return `${String(newHours).padStart(2, '0')}:${String(newMinutes).padStart(2, '0')}`;
    }


    // Выводим текущую дату при загрузке страницы
    updateDateDisplay();
});


// create booking


document.addEventListener("DOMContentLoaded", function () {
    console.log("📌 Скрипт загружен и выполнен");

    const timeSlots = document.querySelectorAll(".time-slot");
    const bookButton = document.querySelector(".book-btn");
    const stadiumId = document.getElementById("stadium-id").innerText.trim();
    const selectedDateElement = document.querySelector(".selected-date");

    console.log(`🏟️ ID стадиона: ${stadiumId}`);

    function parseDate(dateString) {
        // Преобразуем "29 января" в "2025-01-29"
        const months = {
            "января": "01",
            "февраля": "02",
            "марта": "03",
            "апреля": "04",
            "мая": "05",
            "июня": "06",
            "июля": "07",
            "августа": "08",
            "сентября": "09",
            "октября": "10",
            "ноября": "11",
            "декабря": "12"
        };

        const [day, monthName] = dateString.split(" ");
        const month = months[monthName];
        const year = new Date().getFullYear(); // Подставляем текущий год

        return `${year}-${month}-${day.padStart(2, "0")}`; // Приводим к формату YYYY-MM-DD
    }

    // Функция обновления состояния кнопки
    // Функция обновления состояния кнопки
    function updateBookButtonState() {
        const selectedSlots = document.querySelectorAll(".time-slot.selected");
        console.log(`🔄 Обновление кнопки бронирования:`, selectedSlots.length > 0 ? "АКТИВНА" : "НЕ АКТИВНА");

        if (selectedSlots.length > 0) {
            bookButton.removeAttribute("disabled"); // Убираем атрибут disabled
            bookButton.classList.add("active"); // Добавляем класс (если у тебя есть стили для активной кнопки)
        } else {
            bookButton.setAttribute("disabled", "true"); // Добавляем атрибут disabled
            bookButton.classList.remove("active");
        }

        console.log(`📌 Текущий атрибут disabled:`, bookButton.hasAttribute("disabled"));
    }


    // Выбор слотов
    timeSlots.forEach(slot => {
        slot.addEventListener("click", function () {
            if (!slot.classList.contains("booked")) {
                slot.classList.toggle("selected");
                console.log(`🟢 Слот ${slot.dataset.time} ${slot.classList.contains("selected") ? "выбран" : "снят"}`);
                updateBookButtonState();
            } else {
                console.log(`⛔ Попытка выбрать забронированный слот: ${slot.dataset.time}`);
            }
        });
    });

    // Создание бронирования
    async function createBookings() {
        const token = sessionStorage.getItem("authToken");
        if (!token) {
            alert("Ошибка: вы не авторизованы!");
            return;
        }

        const selectedSlots = Array.from(document.querySelectorAll(".time-slot.selected"));

        if (selectedSlots.length === 0) return;

        const formattedDate = parseDate(selectedDateElement.innerText.trim()); // ✅ исправлено

        // Сортируем слоты по времени
        selectedSlots.sort((a, b) => {
            const [aStart] = a.dataset.time.split("-");
            const [bStart] = b.dataset.time.split("-");
            return aStart.localeCompare(bStart);
        });

        // Берем первый и последний слот
        const firstSlot = selectedSlots[0];
        const lastSlot = selectedSlots[selectedSlots.length - 1];

        const [firstStartTime] = firstSlot.dataset.time.split("-");
        const [, lastEndTime] = lastSlot.dataset.time.split("-");

        const bookingData = {
            stadium_id: Number(stadiumId),
            start_time: `${formattedDate}T${firstStartTime}:00.000`,
            end_time: `${formattedDate}T${lastEndTime}:00.000`
        };

        console.log("📤 Отправка бронирования на сервер:", bookingData);

        try {
            const response = await fetch(`${BASE_URL}/booking/create`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(bookingData)
            });

            if (!response.ok) {
                throw new Error("Ошибка бронирования");
            }

            alert("Бронирование успешно!");

            // Обновляем UI
            selectedSlots.forEach(slot => {
                slot.classList.remove("selected");
                slot.classList.add("my-booking");
            });

            bookButton.disabled = true;
        } catch (error) {
            console.error("Ошибка бронирования: ", error);
            alert("Не удалось забронировать. Попробуйте снова.");
        }
    }


    bookButton.addEventListener("click", createBookings);
});


