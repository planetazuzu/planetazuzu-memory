# 📋 1. Consolidación Estratégica del Desarrollo de Athena Pocket (IA Offline Android)

## 🎯 2. Objetivo de la conversación

Definir una guía estructurada para el desarrollo de Athena Pocket, una
aplicación Android 100% offline con IA local, lectura de contenidos
desde tarjeta SD y sistema de consulta tipo Wikipedia offline mediante
RAG.

## 📌 3. Puntos clave tratados

-   Desarrollo de app Android orientada a Galaxy S9 como mínimo.
-   Implementación de IA local usando llama.cpp con modelos GGUF
    cuantizados.
-   Arquitectura basada en React Native + módulos nativos Android.
-   Implementación de sistema RAG offline (embeddings + búsqueda
    híbrida).
-   Uso de SQLite para almacenamiento local estructurado.
-   Gestión de permisos Android mediante Storage Access Framework (SAF).
-   Opciones para integrar Wikipedia offline (ZIM directo vs corpus
    preprocesado).
-   Plan de desarrollo por fases (MVP → optimización).
-   Definición de estructura de carpetas y esquema de base de datos.
-   Consideraciones de rendimiento, energía y privacidad.
-   Checklist de entrega MVP.

## 💡 4. Ideas principales y conclusiones

### Arquitectura Técnica

-   Separación clara entre UI (React Native), lógica de dominio y
    bridges nativos.
-   Inferencia local mediante módulo NDK que envuelve llama.cpp.
-   Persistencia estructurada con SQLite y FTS5.
-   RAG híbrido (vector + texto completo).

### Estrategia RAG

-   Flujo: consulta → recuperación de pasajes → construcción de prompt →
    inferencia local → respuesta con citas.
-   Recomendación inicial: corpus preprocesado para mejorar rendimiento
    y reducir consumo energético.

### Gestión de Recursos

-   Modelos cuantizados 4‑bit/5‑bit para limitar consumo de RAM.
-   Control de hilos (CPU-1).
-   Modo ahorro energético.
-   Detección de espacio antes de instalar paquetes.

### Seguridad y Privacidad

-   Funcionamiento completamente offline.
-   Posibilidad de cifrado local (SQLCipher/Keystore).
-   Exportación e importación de sesiones en formato propio.

### Planificación

-   Desarrollo estructurado en fases (UI → FS → LLM → RAG → Wikipedia →
    optimización).
-   Validar primero con corpus pequeño antes de escalar.

## 📚 5. Recursos y ejemplos compartidos

-   llama.cpp (integración mediante NDK).
-   ONNX Runtime Mobile para embeddings.
-   SQLite + FTS5.
-   react-native-quick-sqlite.
-   Storage Access Framework (Android).
-   Estructura de proyecto recomendada.
-   Plantilla de prompting RAG.
-   Contrato TypeScript para LlamaBridge.
-   Script de ingesta offline para Wikipedia.

## ❓ 6. Preguntas pendientes o acciones sugeridas

-   Decidir modelo inicial GGUF concreto para MVP.
-   Confirmar estrategia definitiva de embeddings (ONNX vs llama.cpp).
-   Elegir enfoque Wikipedia (ZIM directo vs corpus preprocesado).
-   Implementar primer prototipo funcional del LlamaBridge.
-   Preparar corpus mini de validación (100--200 artículos).
-   Validar rendimiento real en Galaxy S9.

## 📝 7. Notas adicionales

-   Proyecto alineado con visión de IA totalmente offline.
-   Diseño enfocado en eficiencia, modularidad y escalabilidad futura.
-   Arquitectura preparada para posible expansión a STT/TTS offline.
