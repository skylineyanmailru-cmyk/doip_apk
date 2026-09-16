
LEAPMOTOR DoIP TESTER — Android GUI v2

Функции:
1. Выбор типа сети: Auto/Ethernet/Wi-Fi/USB Ethernet.
2. DISCOVER Vehicle Identification UDP/13400.
3. VIN/IP/Logical Address/EID/GID.
4. TCP 13400.
5. Routing Activation.
6. Alive Check.
7. FULL TEST — выполняет последовательность автоматически.
8. Пошаговый индикатор:
   Ethernet -> UDP Discovery -> Vehicle Announcement ->
   TCP -> Routing Activation -> Alive Check.
9. Полный HEX TX/RX log.

Сборка APK:
    pip install buildozer
    buildozer android debug

APK будет в bin/.

Для Android:
C11 OBD-II -> DoIP/Ethernet adapter -> RJ45/USB-Ethernet -> Android.

ВАЖНО:
Приложение не выполняет кодирование, программирование ECU и запись параметров.
Оно предназначено для проверки DoIP transport.
