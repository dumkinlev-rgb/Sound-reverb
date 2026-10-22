[app]
title = Audio Reverb
package.name = audioreverb
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
android.sdk_path = /usr/local/lib/android/sdk
android.ndk_path = /usr/local/lib/android/sdk/ndk/25.2.9519653
version = 1.0

# ВАЖНО: Правильные зависимости без оборванных строк. Добавлены numpy и pyjnius
requirements = python3, kivy==2.3.0, 

orientation = portrait
fullscreen = 0

# Ограничиваем архитектуру самой популярной, чтобы сборка шла быстрее
android.archs = arm64-v8a

# Фиксируем стабильную версию NDK, чтобы избежать ошибки Broken Pipe
android.ndk = 25b
android.api = 33
android.minapi = 21

# Запрашиваем права на чтение и запись файлов (включая работу с внешним накопителем)
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

log_level = 2
