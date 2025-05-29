# Исправление проблемы сворачивания сайдбара

## Проблема
При закрытии сайдбара он не полностью скрывался:
- Сайдбар оставался видимым полной ширины
- Содержимое (инструменты и настройки) исчезало
- Оставалась только кнопка открытия
- При повторном открытии сайдбар плавно восстанавливался

## Причина
В CSS были конфликтующие правила:
1. **Основные стили** `.sidebar.collapsed` устанавливали ширину 60px
2. **Мобильные стили** переопределяли поведение и полностью скрывали сайдбар
3. Отсутствовали explicit правила для десктопной версии

### Проблемный код:
```css
@media (max-width: 768px) {
  .sidebar.collapsed {
    transform: translateX(-100%);  /* Полностью скрывал сайдбар */
  }
}
```

## Решение

### 1. Удален конфликтный мобильный стиль
Удалено правило, которое полностью скрывало сайдбар на мобильных устройствах.

### 2. Добавлены explicit десктопные правила
```css
@media (min-width: 769px) {
  .sidebar.collapsed {
    width: 60px !important;
    min-width: 60px !important;
  }
  
  .sidebar.collapsed .sidebar-content {
    overflow: hidden;
  }
  
  .sidebar.collapsed + .chat-container {
    left: 60px !important;
  }
}
```

### 3. Сохранены основные правила
```css
.sidebar.collapsed {
  width: 60px;
  min-width: 60px;
  box-shadow: var(--shadow-sm);
}

.sidebar.collapsed .section-content {
  display: none !important;
}

.sidebar.collapsed + .chat-container {
  left: 60px;
}
```

## Результат

Теперь сайдбар работает правильно:
- ✅ При сворачивании ширина уменьшается до 60px
- ✅ Содержимое полностью скрывается
- ✅ Видна только кнопка сворачивания/разворачивания
- ✅ Chat-область правильно адаптируется (left: 60px)
- ✅ Плавная анимация сворачивания/разворачивания
- ✅ Совместимость с мобильными устройствами сохранена

## Технические детали

### CSS порядок приоритетов:
1. Основные стили для `.sidebar.collapsed`
2. Десктопные media queries `@media (min-width: 769px)`
3. Мобильные media queries `@media (max-width: 768px)`

### Ключевые селекторы:
- `.sidebar.collapsed` - основные стили сворачивания
- `.sidebar.collapsed + .chat-container` - адаптация chat-области
- `.sidebar.collapsed .sidebar-content` - скрытие содержимого 