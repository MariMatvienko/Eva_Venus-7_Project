# Импорт необходимых модулей: krpc для взаимодействия с KSP, time для задержек
import krpc
import time
import pathlib
import csv

# Подключение к KSP через kRPC с именем "Rocket Telemetry Logger"
conn = krpc.connect(
    name='My Example Program',
    address='127.0.0.1',
    rpc_port=50000, stream_port=50001)

# Получение активного корабля
vessel = conn.space_center.active_vessel

# Сохраняем начальную позицию корабля для расчёта смещения
start_position = vessel.position(vessel.orbit.body.reference_frame)
start_time = conn.space_center.ut
# Открываем файл telemetry.txt в режиме записи (если файла нет, он будет создан)
PATH = str(pathlib.Path(__file__).parent.joinpath("telemetry.csv"))
with open(PATH, 'w', newline='') as file:
    # Запись заголовков таблицы в файл
    writer = csv.writer(file)
    writer.writerow(["Time", "Altitude", "Vertical Velocity", "Horizontal Velocity",
                     "Total Velocity", "Drag", "Displacement"])
    time_storage = [0]

    # Вывод сообщения о начале сбора данных
    print("Сбор телеметрии начался. Нажмите Ctrl+C для остановки.")
    print('Запуск через 3...')
    time.sleep(1)
    print('2...')
    time.sleep(1)
    print('1...')
    time.sleep(1)

    vessel.control.sas = False
    vessel.control.rcs = False
    vessel.control.throttle = 1.0

    vessel.control.activate_next_stage()  # Запуск двигателей первой ступени
    vessel.control.activate_next_stage()  # Отсоединение стартовых клемм

    tracking_steps = [7, 5, 4]
    current_steps = 0
    # Бесконечный цикл для постоянного сбора данных
    while True:
        # Текущее время полёта (в секундах с начала игры)
        time_sec = conn.space_center.ut
        elapsed_time = time_sec - start_time
        # Высота над поверхностью планеты (в метрах)
        altitude = vessel.flight().mean_altitude

        # Вертикальная скорость (в м/с) - направление вверх/вниз
        vertical_velocity = vessel.flight(vessel.orbit.body.reference_frame).vertical_speed

        # Горизонтальная скорость (в м/с) - по плоскости поверхности
        horizontal_velocity = vessel.flight(vessel.orbit.body.reference_frame).horizontal_speed

        # Полная скорость (в м/с) - векторная сумма вертикальной и горизонтальной
        total_velocity = vessel.flight(vessel.orbit.body.reference_frame).speed

        # Сила сопротивления воздуха (в ньютонах)
        drag_x, drag_y, drag_z = vessel.flight().drag
        drag = (drag_x ** 2 + drag_y ** 2 + drag_z ** 2) ** 0.5
        # Получаем текущую позицию корабля
        current_position = vessel.position(vessel.orbit.body.reference_frame)

        # Вычисляем вектор смещения от точки старта
        displacement_vector = (
            current_position[0] - start_position[0],  # Смещение по X
            current_position[1] - start_position[1],  # Смещение по Y
            current_position[2] - start_position[2]  # Смещение по Z
        )

        # Вычисляем расстояние от точки старта (модуль вектора смещения)
        displacement = (sum(x ** 2 for x in displacement_vector)) ** 0.5

        # Записываем данные в файл
        if int(elapsed_time) != int(time_storage[-1]):
            writer.writerow([elapsed_time, altitude, vertical_velocity, horizontal_velocity, total_velocity, drag, displacement])

        vessel.auto_pilot.target_roll = 0
        vessel.auto_pilot.engage()
        if altitude < 70000:
            target_pitch = 90 * (1 - altitude / 70000)  # Чем выше высота, тем меньше наклон
            vessel.auto_pilot.target_pitch_and_heading(target_pitch, 90)
        else:
            vessel.auto_pilot.target_pitch_and_heading(0, 90)

        # Проверяем, есть ли топливо в двигателях текущей ступени
        has_fuel = True
        current_stage = vessel.control.current_stage

        # Ищем все двигатели в текущей ступени
        for engine in vessel.parts.engines:
            # Проверяем, принадлежит ли двигатель текущей ступени
            if current_steps <= 2 and engine.part.stage == tracking_steps[current_steps] and not engine.has_fuel:
                has_fuel = False
                break
        # Если топлива нет, активируем следующую ступень
        if not has_fuel and current_steps <= 2:
            vessel.control.activate_next_stage()
            current_steps += 1
            print("Отделение ступени")

        if current_steps == 2:
            current_steps += 1
            vessel.control.activate_next_stage()

        if elapsed_time > 160:
            # vessel.control.activate_next_stage()
            print('Конец')
        # Пауза 0.1 секунды между записями для снижения нагрузки
        time_storage.append(elapsed_time)
        time.sleep(0.1)