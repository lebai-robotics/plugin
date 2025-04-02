/**
 * Toast通知系统
 */
class ToastManager {
  constructor() {
    this.container = null;
    this.createContainer();
  }

  createContainer() {
    if (document.querySelector('.toast-container')) {
      this.container = document.querySelector('.toast-container');
      return;
    }
    
    this.container = document.createElement('div');
    this.container.className = 'toast-container';
    document.body.appendChild(this.container);
  }

  show(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
      'success': '✓',
      'error': '✗',
      'info': 'ℹ',
      'warning': '⚠'
    };
    
    toast.innerHTML = `
      <span class="toast-icon">${iconMap[type] || iconMap.info}</span>
      <span class="toast-message">${message}</span>
    `;
    
    this.container.appendChild(toast);
    
    // 自动移除
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        if (toast.parentNode) {
          this.container.removeChild(toast);
        }
      }, 500);
    }, duration);
  }
  
  success(message, duration) {
    this.show(message, 'success', duration);
  }
  
  error(message, duration) {
    this.show(message, 'error', duration);
  }
  
  info(message, duration) {
    this.show(message, 'info', duration);
  }
  
  warning(message, duration) {
    this.show(message, 'warning', duration);
  }
}

// 创建全局实例
const toast = new ToastManager(); 
