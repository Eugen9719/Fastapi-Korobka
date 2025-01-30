import {loadProfileData} from './profile.js';
import {BASE_URL} from "./config.js";




export async function getUser() {
    const token = sessionStorage.getItem('authToken');
    console.log('getUser: token', token);

    if (!token) {
        console.log('getUser: токен не найден, перенаправляем на страницу логина');
        return;
    }

    console.log('getUser: загружаем данные пользователя...');
    const response = await fetch(`${BASE_URL}/user/me`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}`},
    });


    if (!response.ok) {
        console.log('getUser: ошибка в ответе', response.status);
        if (response.status === 401) {
            alert('Сессия истекла. Пожалуйста, войдите в систему снова.');
            sessionStorage.removeItem('authToken');
            redirectToLogin();
        } else {
            alert(`Ошибка: ${response.statusText}`);

        }
        return null;
    }
    console.log('getUser: данные пользователя успешно получены');
    return response.json();
}


export async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) throw new Error(`Ошибка ${response.status}: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error('Ошибка API:', error);
        alert('Ошибка соединения с сервером.');
        return null;
    }
}
export function isAuthenticated() {
    const token = sessionStorage.getItem('authToken');
    return token !== null

}


// Обновление навигации
function updateNavigation() {
    const navButtons = document.getElementById('navButtons');
    if (!navButtons) return;


    navButtons.innerHTML = isAuthenticated()
        ? `
            
            <a href="${BASE_URL}/profile" class="auth-btn profile-btn">Профиль</a>
        <a href="#" class="auth-btn logout-btn" onclick="logout()">Выйти</a>
        `
        : `
         
            <a href="${BASE_URL}/login" class="auth-btn login-btn">Войти</a>
            <a href="#" class="auth-btn register-btn">Регистрация</a>
        `;
}

// Перенаправление на логин
function redirectToLogin() {
    window.location.href = `${BASE_URL}/login`;
}

// Выход
window.logout = function () {
    sessionStorage.removeItem('authToken');
    updateNavigation();
    window.location.href = `${BASE_URL}/`;
};


// Загрузка страницы
document.addEventListener('DOMContentLoaded', async () => {
    updateNavigation(); // Обновляем навигацию в зависимости от авторизации
    if (isAuthenticated()) {
        await loadProfileData(); // Загружаем данные профиля только если пользователь авторизован
    }
});
