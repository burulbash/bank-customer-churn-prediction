# Bank Customer Churn Prediction

## English

Simple project about bank customer churn.

The project predicts which bank clients may leave soon.
Then it splits them into risk groups and gives simple retention ideas.


## What is inside

- SQL scripts for data preparation
- Python scripts for training models
- churn prediction
- risk segmentation
- simple retention actions
- A/B test plan
- PSI monitoring
- reports and plots
- basic tests

## Tech stack

- Python
- pandas
- numpy
- scikit-learn
- matplotlib
- PostgreSQL / SQL
- pytest


## Project structure

```text
bank-customer-churn-prediction/
├── data/
├── database/
├── sql/
├── src/
├── outputs/
├── tests/
└── requirements.txt
```

## Installation

```bash
git clone https://github.com/burulbash/bank-customer-churn-prediction.git
cd bank-customer-churn-prediction
```

```bash
python -m venv venv
```

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## How to run

Train model:

```bash
python src/train_churn.py --source csv --make-plots
```

Run segmentation:

```bash
python src/run_segmentation.py
```

Create A/B test plan:

```bash
python src/run_ab_test_design.py
```

Run PSI monitoring:

```bash
python src/run_monitoring_psi.py --make-plots
```

## Outputs


```text
outputs/reports/
```

```text
outputs/plots/
```

## Tests

```bash
pytest
```


---

# Прогноз оттока клиентов банка

Простой проект про отток клиентов банка.

Проект предсказывает, какие клиенты могут скоро уйти.
Потом он делит клиентов по уровню риска и предлагает простые идеи для удержания.


## Что есть в проекте

- SQL-скрипты для подготовки данных
- Python-скрипты для обучения моделей
- прогноз оттока
- сегментация по риску
- простые действия для удержания
- план A/B теста
- PSI-мониторинг
- отчеты и графики
- простые тесты

## Технологии

- Python
- pandas
- numpy
- scikit-learn
- matplotlib
- PostgreSQL / SQL
- pytest


## Структура проекта

```text
bank-customer-churn-prediction/
├── data/
├── database/
├── sql/
├── src/
├── outputs/
├── tests/
└── requirements.txt
```

## Установка

```bash
git clone https://github.com/burulbash/bank-customer-churn-prediction.git
cd bank-customer-churn-prediction
```

```bash
python -m venv venv
```

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Как запустить

Обучение модели:

```bash
python src/train_churn.py --source csv --make-plots
```

Сегментация:

```bash
python src/run_segmentation.py
```

A/B тест:

```bash
python src/run_ab_test_design.py
```

PSI-мониторинг:

```bash
python src/run_monitoring_psi.py --make-plots
```

## Результаты

```text
outputs/reports/
```

```text
outputs/plots/
```

## Тесты

```bash
pytest
```
