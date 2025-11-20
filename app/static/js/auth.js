/**
 * Authentication Helper Script
 * Quản lý token, logout, và check authorization
 */

// ✅ Kiểm tra xem người dùng có token không
// Nếu không có và không phải login/register page → redirect login
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const currentPath = window.location.pathname;

    console.log('[AUTH] Current path:', currentPath);
    console.log('[AUTH] Token exists:', !!token);
    if (token) {
        console.log('[AUTH] Token preview:', token.substring(0, 20) + '...');
    }

    // Pages không cần authentication
    const publicPages = ['/', '/login', '/register'];

    if (!token && !publicPages.includes(currentPath)) {
        // Chưa login mà vào page có bảo vệ → redirect login
        console.log('[AUTH] No token, redirecting to login');
        window.location.href = '/login';
    }
}

// ✅ Lấy token từ localStorage
function getToken() {
    const token = localStorage.getItem('access_token');
    if (token) {
        console.log('[AUTH] Token retrieved for request');
    }
    return token;
}

// ✅ Lấy Authorization header
function getAuthHeader() {
    const token = getToken();
    const header = token ? { 'Authorization': `Bearer ${token}` } : {};
    console.log('[AUTH] Header:', header);
    return header;
}

// ✅ Logout - xóa token và redirect
function logout() {
    console.log('[AUTH] Logout called');
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

// ✅ Gọi lúc page load
document.addEventListener('DOMContentLoaded', checkAuth);
