#!/usr/bin/env bash
# install_languagetool.sh - Установка LanguageTool для локального сервера
# Загружает и настраивает LanguageTool из официального источника

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции для вывода
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}           $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Проверка Java
check_java() {
    print_info "Проверка наличия Java..."
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -1)
        print_success "Java найдена: $JAVA_VERSION"
        return 0
    else
        print_warning "Java не найдена"
        return 1
    fi
}

# Установка Java
install_java() {
    print_info "Установка Java..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y default-jre
            print_success "Java установлена"
        elif command -v yum &> /dev/null; then
            sudo yum install -y java-11-openjdk
            print_success "Java установлена"
        else
            print_error "Не удалось определить менеджер пакетов"
            return 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install openjdk
            print_success "Java установлена"
        else
            print_error "Установите Homebrew: https://brew.sh"
            return 1
        fi
    else
        print_error "Неизвестная ОС. Установите Java вручную"
        return 1
    fi
    
    return 0
}

# Скачивание LanguageTool
download_languagetool() {
    local version="$1"
    local cache_dir="$HOME/.cache/language_tool"
    local zip_file="$cache_dir/LanguageTool-${version}.zip"
    local extract_dir="$cache_dir/LanguageTool-${version}"
    
    print_info "Скачивание LanguageTool версии ${version}..."
    
    # Создаём директорию
    mkdir -p "$cache_dir"
    
    # Скачиваем с официального сайта
    cd "$cache_dir"
    
    if wget -q --show-progress "https://languagetool.org/download/LanguageTool-${version}.zip" -O "$zip_file"; then
        print_success "Скачивание завершено"
        
        # Распаковываем
        print_info "Распаковка..."
        unzip -q "$zip_file" -d "$cache_dir"
        
        # Удаляем архив
        rm -f "$zip_file"
        
        # Проверяем, что серверный JAR существует
        if [[ -f "$extract_dir/languagetool-server.jar" ]]; then
            print_success "LanguageTool ${version} установлен в $extract_dir"
            return 0
        else
            print_error "Не найден languagetool-server.jar"
            return 1
        fi
    else
        print_error "Не удалось скачать LanguageTool"
        return 1
    fi
}

# Проверка доступных версий (прямая проверка)
check_versions() {
    print_info "Проверка доступных версий LanguageTool..."
    
    local versions=("6.6" "6.5" "6.4" "6.3")
    local found_version=""
    
    for version in "${versions[@]}"; do
        print_info "Проверка версии ${version}..."
        if wget -q --spider "https://languagetool.org/download/LanguageTool-${version}.zip" 2>/dev/null; then
            found_version="$version"
            print_success "Доступна версия: $found_version"
            break
        fi
    done
    
    if [[ -n "$found_version" ]]; then
        echo "$found_version"
        return 0
    else
        print_error "Не найдено доступных версий"
        return 1
    fi
}

# Настройка переменных окружения
setup_environment() {
    local version="$1"
    local server_dir="$HOME/.cache/language_tool/LanguageTool-${version}"
    
    # Создаём символическую ссылку на текущую версию
    ln -sfn "$server_dir" "$HOME/.cache/language_tool/current"
    
    print_success "Настройка завершена"
}

# Тестирование локального сервера
test_local_server() {
    local version="$1"
    local server_jar="$HOME/.cache/language_tool/LanguageTool-${version}/languagetool-server.jar"
    
    print_info "Тестирование локального сервера..."
    
    if [[ ! -f "$server_jar" ]]; then
        print_error "Файл сервера не найден: $server_jar"
        return 1
    fi
    
    # Запускаем сервер в фоне
    print_info "Запуск LanguageTool сервера (порт 8081)..."
    cd "$(dirname "$server_jar")"
    java -jar languagetool-server.jar --port 8081 &
    SERVER_PID=$!
    
    # Ждём запуска
    sleep 5
    
    # Тестируем
    print_info "Отправка тестового запроса..."
    
    RESPONSE=$(curl -s -X POST "http://localhost:8081/v2/check" \
        -d "language=ru-RU" \
        -d "text=Я пошол в магазин." 2>/dev/null)
    
    # Останавливаем сервер
    kill $SERVER_PID 2>/dev/null || true
    
    # Проверяем ответ
    if [[ "$RESPONSE" == *"matches"* ]]; then
        print_success "Сервер работает корректно"
        return 0
    else
        print_warning "Сервер запустился, но ответ не содержит ожидаемых данных"
        return 0
    fi
}

# Основная функция
main() {
    print_header "Установка LanguageTool для локального сервера"
    
    # Проверяем и устанавливаем Java
    if ! check_java; then
        print_info "Java не найдена. Установка..."
        if install_java; then
            print_success "Java установлена"
        else
            print_error "Не удалось установить Java"
            exit 1
        fi
    fi
    
    # Проверяем доступные версии
    VERSION=$(check_versions)
    if [[ -z "$VERSION" ]]; then
        print_error "Не удалось определить доступную версию"
        exit 1
    fi
    
    print_info "Будет установлена версия: ${VERSION}"
    
    # Скачиваем LanguageTool
    if download_languagetool "$VERSION"; then
        print_success "LanguageTool ${VERSION} установлен"
    else
        print_error "Не удалось установить LanguageTool"
        exit 1
    fi
    
    # Настраиваем окружение
    setup_environment "$VERSION"
    
    # Тестируем
    print_header "Тестирование"
    test_local_server "$VERSION"
    
    print_header "Установка завершена"
    echo ""
    print_info "LanguageTool установлен в: $HOME/.cache/language_tool/LanguageTool-${VERSION}"
    print_info "Для использования в Python:"
    echo ""
    echo "  import language_tool_python"
    echo "  tool = language_tool_python.LanguageTool('ru-RU')"
    echo ""
}

# Запуск
main "$@"