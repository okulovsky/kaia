import { AvatarClient }   from './client.js';
import { Message }        from './message.js';

export class ControlPanelController {
  private trigger: HTMLDivElement;
  private panel: HTMLDivElement;
  private overlay: HTMLDivElement;
  private client: AvatarClient;
  private isOpen: boolean = false;
  private buttons: HTMLButtonElement[] = [];

  constructor(trigger: HTMLDivElement, panel: HTMLDivElement, overlay: HTMLDivElement, client: AvatarClient) {
    this.trigger = trigger;
    this.panel = panel;
    this.overlay = overlay;
    this.client = client;

    this.addButton('↺', () => location.reload());
    this.addButton('📊', () => this.loadPageInOverlay('/phonix-monitor/'));
    this.addButton('🗗', () => this.toggleOverlay());
    this.addButton('❌',  () => window.close());

    this.panel.innerHTML = '';
    this.buttons.forEach(btn => {this.panel.appendChild(btn);});

    this.trigger.addEventListener('click', () => this.togglePanel());
  }

  private addButton(
    label: string,
    onClick: () => void
  ): void {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.classList.add('system-btn');
    btn.addEventListener('click', () => {
      onClick();
      this.hidePanel();
    });
    this.buttons.push(btn);
  }

private async loadPageInOverlay(url: string): Promise<void> {
  // 1) Показываем оверлей (жёстко указываем display),
  //    очищаем содержимое
  this.overlay.style.display = 'block';
  this.overlay.innerHTML = '';

  try {
    // 2) Проверяем доступность URL методом HEAD
    const response = await fetch(url, { method: 'HEAD' });

    if (!response.ok) {
      // 3a) Если статус не 2xx — кидаем ошибку,
      //     которая будет поймана в catch
      throw new Error(`Loading error: ${response.status} ${response.statusText}`);
    }

    // 4) Вставляем страницу через iframe
    const iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = '0';
    this.overlay.appendChild(iframe);

  } catch (err) {
    // 5) В случае любой ошибки показываем её в оверлее
    const message = err instanceof Error
      ? err.message
      : String(err);
    this.overlay.textContent = message;
  }
}

  private toggleOverlay(): void {
    const isHidden = window.getComputedStyle(this.overlay).display === 'none';
    if (isHidden) {
      this.overlay.style.display = '';
    } else {
      this.overlay.style.display = 'none';
    }
  }

  private togglePanel(): void {
    this.isOpen ? this.hidePanel() : this.showPanel();
  }

  private showPanel(): void {
    this.panel.classList.add('open');
    this.isOpen = true;
  }

  private hidePanel(): void {
    this.panel.classList.remove('open');
    this.isOpen = false;
  }
}
