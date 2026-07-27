# Тестирование Booking

1. **Создайте виртуальное окружение** (используем Python 3.11):
   ```bash
   py -3.11 -m venv venv
   ```

2. **Активируйте его:**
   *   **Windows:**
       ```bash
       .\venv\Scripts\activate
       ```
   *   **Linux/macOS:**
       ```bash
       source venv/bin/activate
       ```

3. **Установите зависимости:**
   ```bash
   python.exe -m pip install --upgrade pip
   ```
   ```bash
   pip install -r src/requirements.txt
   ```

4. **запустить Docker**

5. **Запустить все тесты:**
  ```bash
  pytest
  ```