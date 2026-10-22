import os
import wave
import numpy as np
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.utils import platform

# Нативная интеграция с Android для выбора файлов (SAF - Storage Access Framework)
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android import activity
    from jnius import autoclass, cast

    Intent = autoclass('android.content.Intent')
    Activity = autoclass('android.app.Activity')
    Uri = autoclass('android.net.Uri')
    
    # Запрос разрешений при старте
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

KV = '''
MDBoxLayout:
    orientation: 'vertical'
    padding: "20dp"
    spacing: "20dp"
    md_bg_color: self.theme_cls.bg_normal

    MDLabel:
        id: status_label
        text: "Выберите WAV-файл для обработки"
        halign: "center"
        font_style: "H6"
        size_hint_y: None
        height: self.texture_size[1]

    MDRaisedButton:
        text: "Выбрать аудио (.wav)"
        pos_hint: {"center_x": .5}
        on_release: app.open_file_picker()

    MDRaisedButton:
        id: process_btn
        text: "Применить реверберацию и сохранить"
        pos_hint: {"center_x": .5}
        disabled: True
        on_release: app.process_audio()
'''

class ReverbApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.selected_file_path = None
        
        if platform == 'android':
            activity.bind(on_activity_result=self.on_file_selected)
            
        return Builder.load_string(KV)

    def open_file_picker(self):
        """Открывает системный проводник Android или ПК"""
        if platform == 'android':
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.setType("audio/x-wav") # Ограничиваем выбор WAV файлами для простоты
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            currentActivity = cast('android.app.Activity', activity.mActivity)
            currentActivity.startActivityForResult(intent, 1001)
        else:
            # Заглушка для ПК (в реальности на ПК можно использовать plyer.filechooser)
            self.selected_file_path = "test.wav"
            self.root.ids.status_label.text = f"Выбран файл (ПК тестовый): {self.selected_file_path}"
            self.root.ids.process_btn.disabled = False

    def on_file_selected(self, request_code, result_code, intent):
        """Обработчик выбора файла на Android"""
        if request_code == 1001 and result_code == -1: # -1 это Activity.RESULT_OK
            uri = intent.getData()
            # Получаем реальный путь к файлу (на Android 10+ может потребоваться чтение через ContentResolver,
            # для простоты примера берем путь)
            self.selected_file_path = uri.getPath() 
            self.root.ids.status_label.text = f"Файл успешно выбран!"
            self.root.ids.process_btn.disabled = False

    def apply_reverb(self, signal, sample_rate, delay_ms=200, feedback=0.5):
        """Алгоритм реверберации на основе Feedback Delay Line"""
        delay_samples = int(sample_rate * (delay_ms / 1000.0))
        output = np.zeros(len(signal) + delay_samples, dtype=np.int16)
        output[:len(signal)] = signal

        # Эхо-петля обратной связи
        for i in range(delay_samples, len(output)):
            if i < len(signal):
                # Подмешиваем к текущему звуку задержанный фрагмент
                val = int(output[i] + feedback * output[i - delay_samples])
                # Защита от переполнения 16-битного целого числа
                output[i] = max(-32768, min(32767, val))
            else:
                # Дорабатываем затухающий хвост реверберации
                val = int(feedback * output[i - delay_samples])
                output[i] = max(-32768, min(32767, val))
        return output

    def process_audio(self):
        if not self.selected_file_path:
            return

        try:
            self.root.ids.status_label.text = "Обработка аудио..."
            
            # Открываем исходный WAV файл
            with wave.open(self.selected_file_path, 'rb') as wav_in:
                params = wav_in.getparams()
                n_channels, sampwidth, framerate, n_frames = params[:4]
                
                # Читаем байты и переводим в numpy массив (поддерживается 16-bit PCM WAV)
                data = wav_in.readframes(n_frames)
                signal = np.frombuffer(data, dtype=np.int16)

            # Применяем эффект
            processed_signal = self.apply_reverb(signal, framerate)

            # Путь для сохранения результата на Android во внутреннее хранилище приложения
            # Оттуда файл можно будет забрать или отправить
            out_dir = "/sdcard/Download" if platform == 'android' else "."
            output_path = os.path.join(out_dir, "reverb_result.wav")

            # Записываем новый файл
            with wave.open(output_path, 'wb') as wav_out:
                wav_out.setnchannels(n_channels)
                wav_out.setsampwidth(sampwidth)
                wav_out.setframerate(framerate)
                wav_out.writeframes(processed_signal.tobytes())

            self.root.ids.status_label.text = f"Готово! Сохранено в:\n{output_path}"
        except Exception as e:
            self.root.ids.status_label.text = f"Ошибка: {str(e)}"

if __name__ == '__main__':
    ReverbApp().run()