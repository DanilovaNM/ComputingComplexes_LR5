import numpy as np
import threading    # реализация многопоточности
import multiprocessing  # реализация многопроцессорности
import time # измерение времени выполнения операций
from pathlib import Path

# Импорт модулей из ЛР3
from parser import Parser
from solver import DommelSolver

# Расчёт одной схемы
def run_simulation(cfg_path, time_steps):
    """Выполняет симуляцию одной электрической схемы"""
    A, Y, E, J, components, dt = Parser(cfg_path)
    solver = DommelSolver(A, Y, E, J, components, dt)
    
    times, currents, voltages = [], [], []
    
    for _ in range(time_steps):
        U_nodes, I_branches = solver.step()
        times.append(solver.get_time())
        currents.append(I_branches.copy())
        voltages.append(U_nodes.copy())
        
    return np.array(times), np.array(currents), np.array(voltages), dt


# Однопоточный запуск
def process_worker(name, cfg_path, time_steps, result_queue):
    """Рабочая функция для потока: выполняет симуляцию и помещает результат в очередь"""
    result_queue.put((name, run_simulation(cfg_path, time_steps)))

def run_onethread(configs, time_steps):
    """Запускает симуляцию для всех схем в отдельных потоков"""
    # Создание очереди для безопасного обмена данными между потоками
    result_queue = multiprocessing.Queue()
    processes = []
    
    for name, path in configs:
        proc = multiprocessing.Process(target = process_worker, args = (name, path, time_steps, result_queue))
        processes.append(proc)  # добавляем поток в список
        
    for proc in processes: proc.start() # запуск каждого потока
            
    results = {}
    for _ in configs:
        name, result = result_queue.get()   # извлекаем (имя, результат) из очереди
        results[name] = result
        
    for proc in processes: proc.join()  # ожидание завершения каждого потока
        
    return results


# Многопоточный запуск
def thread_worker(name, cfg_path, time_steps, results, lock):
    """Рабочая функция для процесса: выполняет симуляцию и сохраняет результат"""
    result = run_simulation(cfg_path, time_steps)   # симуляция
    
    with lock:  # блокировка: только один поток может изменять results
        results[name] = result

def run_threading(configs, time_steps):
    """Запускает симуляцию для всех схем в отдельных потоках"""
    results = {}
    lock = threading.Lock() # объект блокировки: защита results от одновременного доступа
    threads = []    # список хранения объектов потока
    
    for name, path in configs:
        # Создание нового потока с указанием целевой функции и ее аргументов
        # results и lock передаются по ссылке, чтобы потоки могли работать с одним и тем же объектом
        tpr = threading.Thread(target = thread_worker, args = (name, path, time_steps, results, lock))
        threads.append(tpr)
        
    for tpr in threads: tpr.start() # запуск потоков
    for tpr in threads: tpr.join()  # ожидание завершения каждого потока
        
    return results


# Многопроцессорный запуск
def run_multiprocessing(configs, time_steps):
    """Запускает симуляцию для всех схем последовательно в одном процессе"""
    results = {}    # словарь для хранения результатов
    
    for name, path in configs:
        print(f"Расчёт: {name}")
        results[name] = run_simulation(path, time_steps)
    return results


def main():
    """Основная функция программы: запускает симуляции в разных режимах,
    сравнивает время выполнения и сохраняет графики"""
    
    time_steps = 1000   # кол-во временных шагов для каждой симуляции

    tests_dir = Path(__file__).parent / "tests"
    json_files = list(tests_dir.glob("*.json"))

    # Формирование списока: (имя_файла_без_расширения, полный_путь_к_файлу)
    configs = [(f.stem, str(f.resolve())) for f in json_files]
    print(f"Найдено схем для расчёта: {len(configs)}")


    # 1. Однопоточный режим
    print("\n1. Однопоточный режим запущен...")
    t0 = time.perf_counter()
    results_mp = run_onethread(configs, time_steps)   # запуск симуляции в однопоточном режиме
    t_single = time.perf_counter() - t0
    
    # 2. Многопоточный режим
    print("\n2. Многопоточный режим запущен...")
    t0 = time.perf_counter()
    results_threads = run_threading(configs, time_steps)    # запуск симуляции в многопоточном режиме
    t_threads = time.perf_counter() - t0  
    
    # 3. Многопроцессорный режим
    print("\n3. Многопроцессорный режим запущен...")
    t0 = time.perf_counter()    # начало отсчета
    results_single = run_multiprocessing(configs, time_steps) # запуск симуляции в однопоточном режиме
    t_mp = time.perf_counter() - t0

    # Вывод сравнительной таблицы
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ЗАМЕРОВ ВРЕМЕНИ")
    print("=" * 50)
    print(f"Однопоточный:   {t_single:.5f} с")
    print(f"Многопоточный:  {t_threads:.5f} с")
    print(f"Многопроцессорный:   {t_mp:.5f} с")
    print("=" * 50)

        

if __name__ == "__main__":
    main()