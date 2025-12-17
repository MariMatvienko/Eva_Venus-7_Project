import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# ---------- Константы ----------
g = 9.81
rho_0 = 1.225
G = 6.67430e-11
M_kerbin = 5.2915793e22
R_kerbin = 600_000
C_d = 2.0

stages = [
    {"wet_mass": 117_000, "fuel_mass": 101_000, "thrust": 2_816_500,
     "burn_time": 90, "ejection_force": 100, "area": 10.0},
    {"wet_mass": 63_800, "fuel_mass": 33_400, "thrust": 875_820,
     "burn_time": 47, "ejection_force": 100, "area": 8.0},
]

# ---------- Функции ----------
def air_density(h):
    return rho_0 * np.exp(-h / 4000)

def calculate_pitch(altitude):
    return 90 * (1 - altitude / 70000) if altitude < 70_000 else 0

def gravitational_acceleration(height):
    r = R_kerbin + height
    return G * M_kerbin / r ** 2

def rocket_equations(y, t, stage_index):
    x, vx, y_, vy = y
    stage = stages[stage_index]
    fuel_mass = stage["fuel_mass"]
    thrust = stage["thrust"]
    burn_time = stage["burn_time"]
    drain_speed = fuel_mass / burn_time
    ejection_force = stage["ejection_force"]
    area = stage["area"]

    cur_mass = start_mass - drain_speed * t
    vel2 = vx**2 + vy**2
    pitch = calculate_pitch(y_)

    # Силы
    gravity = cur_mass * gravitational_acceleration(y_)
    drag = 0.5 * C_d * air_density(y_) * vel2 * area
    radius = R_kerbin + y_
    centrifugal = cur_mass * vx**2 / radius

    a_vert = ((thrust - drag) * np.sin(np.radians(pitch)) + centrifugal - gravity) / cur_mass
    a_horiz = ((thrust - drag) * np.cos(np.radians(pitch))) / cur_mass

    # После окончания сжигания топлива
    if t >= burn_time - 7:
        a_horiz += (ejection_force / cur_mass) * np.cos(np.radians(pitch))
        a_vert   += (ejection_force / cur_mass) * np.sin(np.radians(pitch))
        print(a_horiz, a_vert, 'burn_time !!!')

    return [vx, a_horiz, vy, a_vert]

# ---------- Интегрирование ----------
# первая ступень
start_mass = 209_946                     # общая начальная масса
t1 = np.linspace(0, stages[0]["burn_time"], 1000)
res1 = odeint(rocket_equations, [0, 0, 0, 0], t1, args=(0,))

# вторая ступень (масса уже без топлива первой)
start_mass = stages[1]["wet_mass"]
t2 = np.linspace(0, stages[1]["burn_time"], 1000)
res2 = odeint(rocket_equations, res1[-1, :], t2, args=(1,))

# объединяем
time = np.concatenate([t1, t1[-1] + t2])
y_coords = np.concatenate([res1[:, 2], res2[:, 2]])
x_coords = np.concatenate([res1[:, 0], res2[:, 0]])
x_vel    = np.concatenate([res1[:, 1], res2[:, 1]])
y_vel    = np.concatenate([res1[:, 3], res2[:, 3]])
speed_coords = np.sqrt(x_vel**2 + y_vel**2)
Displacement_coords = np.sqrt(x_coords**2 + y_coords**2)

# ---------- Чтение данных из файла ----------
try:
    # Пробуем разные разделители
    print("Попытка чтения файла...")
    
    # Сначала пробуем прочитать как обычный текст для анализа
    with open('ksp_flight_data.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Первые 3 строки файла:")
        for i, line in enumerate(lines[:3]):
            print(f"Строка {i}: {line.strip()}")
        
        # Анализируем разделитель по первой строке (заголовку)
        header = lines[0].strip()
        if '\t' in header:
            delimiter = '\t'
            print("Обнаружен разделитель: табуляция")
        elif ',' in header:
            delimiter = ','
            print("Обнаружен разделитель: запятая")
        else:
            delimiter = None  # пробуем автоматическое определение
            print("Разделитель не обнаружен, пробуем автоопределение")
        
        # Подсчитываем количество столбцов
        if delimiter:
            columns = header.split(delimiter)
            print(f"Количество столбцов: {len(columns)}")
            print(f"Столбцы: {columns}")
    
    # Читаем данные из CSV файла с определенным разделителем
    if delimiter:
        data = np.genfromtxt('ksp_flight_data.csv', delimiter=delimiter, skip_header=1)
    else:
        data = np.genfromtxt('ksp_flight_data.csv', skip_header=1)
    
    print(f"Форма данных: {data.shape}")
    print(f"Первые 5 строк данных:")
    print(data[:5])
    
    # Проверяем размерность данных
    if len(data.shape) == 1:
        print("Внимание: данные одномерные. Возможно в файле только одна строка.")
        # Если данные одномерные, преобразуем в двумерный массив с одной строкой
        data = data.reshape(1, -1)
        print(f"Новая форма данных: {data.shape}")
    
    # Извлекаем данные из файла (согласно порядку столбцов)
    # Time, Altitude, Vertical Velocity, Horizontal Velocity, Total Velocity, Drag, Displacement
    query_times = data[:, 0]  # Time
    alt_norm = data[:, 1]     # Altitude
    Vertical_Velocity_norm = data[:, 2]  # Vertical Velocity
    Horizontal_Velocity_norm = data[:, 3]  # Horizontal Velocity
    Total_Velocity_norm = data[:, 4]  # Total Velocity
    # data[:, 5] это Drag - не используем
    Displacement_norm = data[:, 6]  # Displacement
    
    print(f"Количество точек времени: {len(query_times)}")
    print(f"Диапазон времени: от {query_times[0]} до {query_times[-1]} сек")
    
except Exception as e:
    print(f"Ошибка при чтении файла: {e}")
    print("Используем тестовые данные...")
    
    # Создаем тестовые данные для продолжения работы
    query_times = np.linspace(0, 150, 100)
    alt_norm = 100 * query_times
    Vertical_Velocity_norm = 50 * np.sin(query_times * 0.1)
    Horizontal_Velocity_norm = 20 * query_times
    Total_Velocity_norm = np.sqrt(Vertical_Velocity_norm**2 + Horizontal_Velocity_norm**2)
    Displacement_norm = 0.5 * 10 * query_times**2

# -------------------------------------------------
# Интерполяция
# -------------------------------------------------
alt_at_query = np.interp(query_times, time, y_coords, left=np.nan, right=np.nan)
Horizontal_Velocity_norm_query = np.interp(query_times, time, x_vel, left=np.nan, right=np.nan)
Total_Velocity_norm_query = np.interp(query_times, time, speed_coords, left=np.nan, right=np.nan)
Vertical_Velocity_norm_query = np.interp(query_times, time, y_vel, left=np.nan, right=np.nan)
Displacement_norm_query = np.interp(query_times, time, Displacement_coords, left=np.nan, right=np.nan)

# Создание графиков
fig = plt.figure(figsize=(15, 10))

# График высоты
plt.subplot(3, 2, 1)
plt.plot(query_times, alt_at_query, label="Высота (м)")
plt.plot(query_times, alt_norm, label='Высота (м) ksp', color='orange')
plt.title('Высота от времени')
plt.xlabel('Время (с)')
plt.ylabel('Высота (м)')
# 2) Ошибка
err = alt_norm - alt_at_query
mask = ~np.isnan(err)   # игнорируем NaN‑ы
plt.plot(query_times[mask], err[mask], label='Погрешность', color='tab:grey', linewidth=2)
plt.legend()
plt.grid(True, alpha=0.3)  # Добавлена сетка с прозрачностью

# График вертикальной скорости
plt.subplot(3, 2, 2)
plt.plot(query_times, Vertical_Velocity_norm_query, label='Скорость по вертикали', color='green')
plt.plot(query_times, Vertical_Velocity_norm, label='Скорость по вертикали ksp', color='red')
plt.title('Скорость по вертикали от времени')
plt.xlabel('Время (с)')
plt.ylabel('Скорость (м/с)')
# 2) Ошибка
err = Vertical_Velocity_norm - Vertical_Velocity_norm_query
mask = ~np.isnan(err)   # игнорируем NaN‑ы
plt.plot(query_times[mask], err[mask], label='Погрешность', color='tab:grey', linewidth=2)
plt.legend()
plt.grid(True, alpha=0.3)  # Добавлена сетка с прозрачностью

# График горизонтальной скорости
plt.subplot(3, 2, 3)
plt.plot(query_times, Horizontal_Velocity_norm_query, label='Скорость по горизонтали', color='blue')
plt.plot(query_times, Horizontal_Velocity_norm, label='Скорость по горизонтали ksp', color='orange')
plt.title('Скорость по горизонтали от времени')
plt.xlabel('Время (с)')
plt.ylabel('Скорость (м/с)')
# 2) Ошибка
err = Horizontal_Velocity_norm - Horizontal_Velocity_norm_query
mask = ~np.isnan(err)   # игнорируем NaN‑ы
plt.plot(query_times[mask], err[mask], label='Погрешность', color='tab:grey', linewidth=2)
plt.legend()
plt.grid(True, alpha=0.3)  # Добавлена сетка с прозрачностью

# График скорости
plt.subplot(3, 2, 4)
plt.plot(query_times, Total_Velocity_norm_query, label="Скорость (м/с)")
plt.plot(query_times, Total_Velocity_norm, label="Скорость (м/с) ksp", color='orange')
plt.title('Скорость от времени')
plt.xlabel('Время (с)')
plt.ylabel('Скорость (м/с)')
# 2) Ошибка
err = Total_Velocity_norm - Total_Velocity_norm_query
mask = ~np.isnan(err)   # игнорируем NaN‑ы
plt.plot(query_times[mask], err[mask], label='Погрешность', color='tab:grey', linewidth=2)
plt.legend()
plt.grid(True, alpha=0.3)  # Добавлена сетка с прозрачностью

# График смещения
plt.subplot(3, 2, 5)
plt.plot(query_times, Displacement_norm_query, label="Смещение")
plt.plot(query_times, Displacement_norm, label="Смещение ksp", color='orange')
plt.title('Смещение от времени')
plt.xlabel('Время (с)')
plt.ylabel('Смещение (м)')
# 2) Ошибка
err = Displacement_norm - Displacement_norm_query
mask = ~np.isnan(err)   # игнорируем NaN‑ы
plt.plot(query_times[mask], err[mask], label='Погрешность', color='tab:grey', linewidth=2)
plt.legend()
plt.grid(True, alpha=0.3)  # Добавлена сетка с прозрачностью

plt.tight_layout()
plt.show()