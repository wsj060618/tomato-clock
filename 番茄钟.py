import tkinter as tk
from tkinter import messagebox, simpledialog
import time

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄钟")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", 1)
        self.root.configure(bg="#2D2D2D")

        # 窗口拖动功能
        self._offset_x = 0
        self._offset_y = 0
        self.root.bind('<Button-1>', self.on_drag_start)
        self.root.bind('<B1-Motion>', self.on_drag_motion)

        # 按钮设置
        self.setup_buttons()

        # 计时设置
        self.work_duration = 25 * 60
        self.break_duration = 5 * 60
        self.current_duration = self.work_duration
        self.is_working = True
        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.countdown_mode = True  # 默认倒计时模式

        # 界面元素
        self.setup_ui()
        self.update_display()
        self.set_window_position()

        # 小球悬浮窗
        self.ball_window = None
        self.ball_radius = 30  # 增大半径以显示时间
        self.ball_x_offset = 0
        self.ball_y_offset = 0

    def setup_buttons(self):
        # 关闭按钮
        self.close_btn = tk.Label(self.root, text="×", font=('Arial', 18),
                                 fg='white', bg='#2D2D2D', cursor="hand2")
        self.close_btn.place(relx=1.0, x=-5, y=5, anchor='ne', width=30, height=30)
        self.close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(bg='#4D4D4D'))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(bg='#2D2D2D'))

        # 最小化按钮
        self.minimize_btn = tk.Label(self.root, text="-", font=("Arial", 18),
                                    fg='white', bg='#2D2D2D', cursor="hand2")
        self.minimize_btn.place(relx=1.0, x=-35, y=5, anchor='ne', width=30, height=30)
        self.minimize_btn.bind("<Button-1>", lambda e: self.custom_iconify())
        self.minimize_btn.bind("<Enter>", lambda e: self.minimize_btn.config(bg='#4D4D4D'))
        self.minimize_btn.bind("<Leave>", lambda e: self.minimize_btn.config(bg='#2D2D2D'))

    def setup_ui(self):
        # 时间显示
        self.time_label = tk.Label(self.root, font=('Helvetica', 32),
                                  fg='#FFFFFF', bg='#2D2D2D')
        self.time_label.pack(pady=20)

        # 状态显示
        self.status_label = tk.Label(self.root, font=('Helvetica', 12),
                                    fg='#FF6B6B', bg='#2D2D2D')
        self.status_label.pack(pady=10)

        # 按钮框架
        button_frame = tk.Frame(self.root, bg='#2D2D2D')
        button_frame.pack(pady=10)

        # 开始/暂停按钮
        self.start_pause_btn = tk.Button(button_frame, text="开始",
                                        command=self.toggle_timer,
                                        font=('Helvetica', 12),
                                        fg='white', bg='#3D3D3D',
                                        activeforeground='white',
                                        activebackground='#4D4D4D',
                                        relief=tk.FLAT)
        self.start_pause_btn.pack(side=tk.LEFT, padx=5)

        # 重置按钮
        self.reset_btn = tk.Button(button_frame, text="重置",
                                  command=self.reset_timer,
                                  font=('Helvetica', 12),
                                  fg='white', bg='#3D3D3D',
                                  activeforeground='white',
                                  activebackground='#4D4D4D',
                                  relief=tk.FLAT)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # 设置按钮
        self.settings_btn = tk.Button(button_frame, text="设置",
                                     command=self.show_settings,
                                     font=('Helvetica', 12),
                                     fg='white', bg='#3D3D3D',
                                     activeforeground='white',
                                     activebackground='#4D4D4D',
                                     relief=tk.FLAT)
        self.settings_btn.pack(side=tk.LEFT, padx=5)

        # 计时模式按钮
        self.mode_btn = tk.Button(button_frame, text="倒计时",
                                 command=self.toggle_mode,
                                 font=('Helvetica', 12),
                                 fg='white', bg='#3D3D3D',
                                 activeforeground='white',
                                 activebackground='#4D4D4D',
                                 relief=tk.FLAT)
        self.mode_btn.pack(side=tk.LEFT, padx=5)

    def toggle_mode(self):
        self.countdown_mode = not self.countdown_mode
        self.mode_btn.config(text="倒计时" if self.countdown_mode else "正计时")
        print(f"当前计时模式: {'倒计时' if self.countdown_mode else '正计时'}")
        self.reset_timer()

    def set_window_position(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - 250
        y = 50
        self.root.geometry(f'+{x}+{y}')

    def on_drag_start(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def on_drag_motion(self, event):
        x = self.root.winfo_x() + event.x - self._offset_x
        y = self.root.winfo_y() + event.y - self._offset_y
        self.root.geometry(f'+{x}+{y}')

    def toggle_timer(self):
        if self.is_running:
            self.is_running = False
            self.start_pause_btn.config(text="继续")
            self.elapsed_time += time.time() - self.start_time
        else:
            self.is_running = True
            self.start_pause_btn.config(text="暂停")
            self.start_time = time.time()
            self.update()

    def update(self):
        if self.is_running:
            if self.countdown_mode:
                current = self.current_duration - (self.elapsed_time + (time.time() - self.start_time))
                if current <= 0:
                    self.switch_phase()
                else:
                    self.update_display(current)
                    self.root.after(1000, self.update)
                    if self.ball_window:
                        self.update_ball_display(current)
            else:
                current = self.elapsed_time + (time.time() - self.start_time)
                if current >= self.current_duration:
                    self.switch_phase()
                else:
                    self.update_display(current)
                    self.root.after(1000, self.update)
                    if self.ball_window:
                        self.update_ball_display(current)

    def update_display(self, current=None):
        if current is None:
            if self.countdown_mode:
                current = self.current_duration - self.elapsed_time
            else:
                current = self.elapsed_time
        minutes = int(current // 60)
        seconds = int(current % 60)
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        status = "工作中" if self.is_working else "休息中"
        self.status_label.config(text=status, fg='#FF6B6B' if self.is_working else '#6BFF6B')

    def switch_phase(self):
        self.is_running = False
        self.start_pause_btn.config(text="开始")
        self.elapsed_time = 0
        self.is_working = not self.is_working
        self.current_duration = self.break_duration if self.is_working else self.work_duration
        messagebox.showinfo("时间到！", "休息时间到" if self.is_working else "工作时间结束")
        self.update_display()

    def reset_timer(self):
        self.is_running = False
        self.start_pause_btn.config(text="开始")
        self.elapsed_time = 0
        self.is_working = True
        self.current_duration = self.work_duration
        self.update_display()

    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置时间")
        settings_window.configure(bg="#2D2D2D")
        # 设置窗口大小和主界面相近
        settings_window.geometry("250x200")
        
        # 添加拖动功能
        _offset_x = 0
        _offset_y = 0
        
        def on_drag_start(event):
            nonlocal _offset_x, _offset_y
            _offset_x = event.x
            _offset_y = event.y

        def on_drag_motion(event):
            x = settings_window.winfo_x() + event.x - _offset_x
            y = settings_window.winfo_y() + event.y - _offset_y
            settings_window.geometry(f"+{x}+{y}")

        settings_window.bind('<Button-1>', on_drag_start)
        settings_window.bind('<B1-Motion>', on_drag_motion)

        # 工作时间设置
        tk.Label(settings_window, text="工作时间（分钟）:", font=('Helvetica', 12),
                 fg='white', bg='#2D2D2D').pack(pady=8, padx=20)
        work_entry = tk.Entry(settings_window, font=('Helvetica', 12), bg="#2D2D2D", fg="white", insertbackground='white')
        work_entry.insert(0, str(self.work_duration // 60))
        work_entry.pack(pady=5, padx=20)

        # 休息时间设置
        tk.Label(settings_window, text="休息时间（分钟）:", font=('Helvetica', 12),
                 fg='white', bg='#2D2D2D').pack(pady=8, padx=20)
        break_entry = tk.Entry(settings_window, font=('Helvetica', 12), bg="#2D2D2D", fg="white", insertbackground='white')
        break_entry.insert(0, str(self.break_duration // 60))
        break_entry.pack(pady=5, padx=20)

        def save_settings():
            try:
                work = int(work_entry.get())
                break_time = int(break_entry.get())
                if work > 0 and break_time > 0:
                    self.work_duration = work * 60
                    self.break_duration = break_time * 60
                    if self.is_working:
                        self.current_duration = self.work_duration
                    else:
                        self.current_duration = self.break_duration
                    self.reset_timer()
                    settings_window.destroy()
            except ValueError:
                messagebox.showerror("输入错误", "请输入有效的整数")

        tk.Button(settings_window, text="保存", command=save_settings,
                 font=('Helvetica', 11), fg='white', bg='#3D3D3D',
                 activeforeground='white', activebackground='#4D4D4D',
                 relief=tk.FLAT, width=6, height=4).pack(pady=20)

    def update_ball_display(self, current=None):
        if current is None:
            if self.countdown_mode:
                current = self.current_duration - self.elapsed_time
            else:
                current = self.elapsed_time
        minutes = int(current // 60)
        seconds = int(current % 60)
        self.ball_time_label.config(text=f"{minutes:02d}:{seconds:02d}")

    def custom_iconify(self):
        self.root.withdraw()
        self.create_ball_window()

    def create_ball_window(self):
        if self.ball_window is None:
            self.ball_window = tk.Toplevel(self.root)
            self.ball_window.overrideredirect(True)
            self.ball_window.wm_attributes("-topmost", 1)
            self.ball_window.wm_attributes("-transparentcolor", "#000000")

            # 计算小球位置
            screen_width = self.ball_window.winfo_screenwidth()
            x = screen_width - self.ball_radius * 2 - 10
            y = 10

            self.ball_window.geometry(f"{self.ball_radius * 2}x{self.ball_radius * 2}+{x}+{y}")

            canvas = tk.Canvas(self.ball_window, width=self.ball_radius * 2, height=self.ball_radius * 2, bg="#000000", highlightthickness=0)
            canvas.pack()
            canvas.create_oval(0, 0, self.ball_radius * 2, self.ball_radius * 2, fill="#2D2D2D")  # 统一背景色

            # 时间显示
            self.ball_time_label = tk.Label(self.ball_window, font=('Helvetica', 10),
                                          fg='#FFFFFF', bg='#2D2D2D')
            self.ball_time_label.place(relx=0.5, rely=0.5, anchor='center')
            self.update_ball_display(self.current_duration if self.countdown_mode else 0)
            
            self.ball_window.bind("<Button-1>", self.on_ball_drag_start)
            self.ball_window.bind("<B1-Motion>", self.on_ball_drag_motion)
            self.ball_window.bind("<Double-Button-1>", self.restore_from_ball)

    def on_ball_drag_start(self, event):
        self.ball_x_offset = event.x
        self.ball_y_offset = event.y

    def on_ball_drag_motion(self, event):
        x = self.ball_window.winfo_x() + event.x - self.ball_x_offset
        y = self.ball_window.winfo_y() + event.y - self.ball_y_offset
        self.ball_window.geometry(f"+{x}+{y}")

    def restore_from_ball(self, event):
        if self.ball_window:
            self.ball_window.destroy()
            self.ball_window = None
            self.root.deiconify()

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()