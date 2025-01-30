// config.js
export const BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const months = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
];

// Функция для форматирования даты
export function formatDate(isoDate) {
    const date = new Date(isoDate);
    const options = {day: 'numeric', month: 'long', year: 'numeric'};
    return date.toLocaleDateString('ru-RU', options);
}

// Функция для форматирования времени
export function formatTime(isoDate) {
    const date = new Date(isoDate);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}
