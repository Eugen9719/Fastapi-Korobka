import {apiRequest, getUser} from './base.js';
import {BASE_URL, formatDate, formatTime} from './config.js';

function updateProfile(user) {
    const profileName = document.querySelector('.profile-name');
    const profileStatus = document.querySelector('.profile-email');
    if (profileName) profileName.textContent = user.first_name;
    if (profileStatus) profileStatus.textContent = user.email;
}

async function deleteBooking(bookingId, token) {
    try {
        const response = await fetch(`${BASE_URL}/booking/delete/${bookingId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
        });

        if (response.ok) {
            console.log('Бронирование удалено');
            return true;
        } else {
            console.error('Ошибка при удалении бронирования', response.status);
            return false;
        }
    } catch (error) {
        console.error('Ошибка сети при удалении бронирования', error);
        return false;
    }
}

export async function loadProfileData() {
    try {
        const user = await getUser();
        if (!user) return;

        updateProfile(user);

        const token = sessionStorage.getItem('authToken');
        const bookings = await apiRequest(`${BASE_URL}/booking/read`, {
            method: 'GET',
            headers: {'Authorization': `Bearer ${token}`}
        });

        const bookingHistoryDiv = document.querySelector('.booking-history');
        if (!bookingHistoryDiv) return;

        bookingHistoryDiv.innerHTML = ''; // Очищаем перед добавлением

        bookings.forEach(booking => {
            const formattedDate = formatDate(booking.start_time);
            const formattedTime = `${formatTime(booking.start_time)} - ${formatTime(booking.end_time)}`;

            bookingHistoryDiv.innerHTML += `
                <div class="booking-card" data-booking-id="${booking.id}">
                    <div class="stadium-name">${booking.stadium.name}</div>
                    <div class="booking-content">
                        <img src="stadium1.jpg" alt="Стадион" class="booking-image">
                        <div class="date-address">
                            <div><strong>Дата:</strong> <span>${formattedDate}</span></div>
                            <div><strong>Адрес:</strong> <span>${booking.stadium.address}</span></div>
                        </div>
                        <div class="time-price">
                            <div><strong>Время:</strong> <span>${formattedTime}</span></div>
                            <div><strong>Цена:</strong> <span>${booking.price}</span></div>
                        </div>
                        <button class="cancel-btn" data-booking-id="${booking.id}">Отменить</button>
                    </div>
                </div>`;
        });

        // Добавляем обработчики событий для всех кнопок "Отменить"
        document.querySelectorAll('.cancel-btn').forEach(button => {
            button.addEventListener('click', async () => {
                const bookingId = button.dataset.bookingId;
                if (confirm('Вы уверены, что хотите отменить бронирование?')) {

                    const isDeleted = await deleteBooking(bookingId, token);
                    if (isDeleted) {
                        const bookingElement = document.querySelector(`[data-booking-id="${bookingId}"]`);
                        bookingElement.remove();
                    }
                }
            });
        });
    } catch (error) {
        console.error('Ошибка загрузки данных профиля', error);
    }
}

