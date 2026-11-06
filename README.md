# Cargo Dependency Visualizer — вариант 19

Проект реализует пять этапов практической работы: чтение конфигурации XML,
получение прямых зависимостей через API crates.io, построение графа,
поиск обратных зависимостей и визуализацию в Mermaid/SVG.

## Состав проекта

```text
cargo-dependency-visualizer/
├── config.xml
├── main.py
├── dependency_service.py
├── graph_service.py
├── visualization_service.py
├── package.json
├── .gitignore
├── examples/
│   └── test_repository.json
└── output/
```

## Требования

- Python 3.9 или новее
- Node.js и npm
- Доступ к сети для реального режима crates.io

Python-код использует только стандартные библиотеки. Для преобразования
Mermaid в SVG используется Mermaid CLI.

## Установка

В терминале перейдите в корневую папку проекта и выполните:

```bash
npm install
```

Проверка:

```bash
npx mmdc --version
```

## Запуск

```bash
python3 main.py
```

По умолчанию конфигурация настроена на тестовый граф `A`:

```xml
<package_name>A</package_name>
<test_mode>true</test_mode>
<max_depth>3</max_depth>
<filter_substring></filter_substring>
<output_file>output/dependencies.svg</output_file>
```

После запуска программа выводит параметры, граф, обратные зависимости,
сохраняет Mermaid-код в `output/dependencies.mmd` и изображение в
`output/dependencies.svg`.

## Параметры XML

| Параметр | Назначение |
|---|---|
| `package_name` | Имя исходного пакета |
| `repository_url` | Адрес API репозитория |
| `test_repository_path` | Путь к тестовому JSON |
| `test_mode` | `true` — тестовый граф, `false` — API |
| `package_version` | Версия исходного пакета |
| `output_file` | Путь к SVG |
| `max_depth` | Максимальная глубина обхода |
| `filter_substring` | Подстрока, исключаемая из имён зависимостей |

## Три демонстрации для этапа 5

Перед каждой демонстрацией изменяйте соответствующие значения в `config.xml`.
Чтобы сохранить результаты, меняйте `output_file` на отдельное имя.

### Демонстрация 1 — полный тестовый граф

```xml
<package_name>A</package_name>
<test_mode>true</test_mode>
<max_depth>3</max_depth>
<filter_substring></filter_substring>
<output_file>output/demo1.svg</output_file>
```

Ожидаемые связи:

```text
A -> B, C
B -> D
C -> D, E
D -> A
E -> F
F -> нет зависимостей
```

### Демонстрация 2 — фильтрация пакета E

```xml
<package_name>A</package_name>
<test_mode>true</test_mode>
<max_depth>3</max_depth>
<filter_substring>E</filter_substring>
<output_file>output/demo2.svg</output_file>
```

Ожидаемые связи:

```text
A -> B, C
B -> D
C -> D
D -> A
```

Пакет E исключён, поэтому F также не достигается из исходного пакета.

### Демонстрация 3 — ограничение глубины

```xml
<package_name>A</package_name>
<test_mode>true</test_mode>
<max_depth>2</max_depth>
<filter_substring></filter_substring>
<output_file>output/demo3.svg</output_file>
```

Ожидаемые связи:

```text
A -> B, C
B -> D
C -> D, E
D -> нет зависимостей
E -> нет зависимостей
```

После каждой демонстрации запускайте `python3 main.py`. Верните `config.xml`
к исходным настройкам, если продолжаете обычную работу с проектом.

## Реальный режим crates.io

Для получения данных из API измените:

```xml
<package_name>serde</package_name>
<test_mode>false</test_mode>
<package_version>1.0.0</package_version>
```

В реальном режиме программа получает зависимости исходного пакета указанной
версии, а для транзитивных пакетов запрашивает их текущую максимальную версию
через API crates.io. Поэтому граф транзитивных зависимостей может отличаться
от дерева Cargo, разрешённого для конкретного Rust-проекта.

## Сравнение с Cargo

В корне Rust-проекта, где подключён нужный crate, можно выполнить:

```bash
cargo tree
```

Для обратного дерева:

```bash
cargo tree -i serde
```

Сравнивайте графы только при одинаковом исходном пакете и сопоставимых
версиях. Возможные причины расхождений:

1. Cargo строит дерево для конкретного проекта и его `Cargo.lock`, а этот
   инструмент получает опубликованные сведения через API crates.io.
2. Для транзитивных пакетов инструмент запрашивает максимальную версию,
   а Cargo выбирает версию, удовлетворяющую ограничениям зависимостей.
3. Cargo учитывает особенности платформы, features и разрешение версий.
   Реализация учебного проекта не моделирует все эти правила.
4. В графе учебного проекта могут применяться собственные ограничения
   глубины и фильтр по подстроке.

Тестовые узлы `A`, `B`, `C` и т. д. являются условными и не предназначены
для сравнения с реальным `cargo tree`.

## Коммиты по этапам

Примеры сообщений коммитов, если этапы сохраняются отдельно:

```bash
git add config.xml main.py .gitignore examples/test_repository.json
git commit -m "feat(config): implement stage 1 configuration prototype"

git add main.py dependency_service.py config.xml
git commit -m "feat(dependencies): retrieve direct package dependencies"

git add main.py graph_service.py dependency_service.py config.xml examples/test_repository.json
git commit -m "feat(graph): implement BFS dependency graph traversal"

git add main.py graph_service.py
git commit -m "feat(graph): implement reverse dependency search"

git add main.py visualization_service.py package.json README.md
git commit -m "feat(visualization): export dependency graph to SVG"
```

Если предыдущие этапы уже закоммичены, не повторяйте их коммиты — добавьте
только новые/изменённые файлы пятого этапа.
