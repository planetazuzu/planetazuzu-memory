
# 📋 1. Desarrollo estructural de Athena Pocket (Demo y Pro) con enfoque IA Offline estilo militar retro

## 🎯 2. Objetivo de la conversación
Definir la estructura de desarrollo de dos aplicaciones (Athena Pocket Demo y Athena Pocket Pro) basadas en IA offline almacenada en dispositivos físicos (pendrive/microSD), con estética militar retro, utilizando Vibe Coding para la base visual y Cursor para la implementación técnica final.

## 📌 3. Puntos clave tratados

- Desarrollo de dos apps separadas: Demo (gratuita) y Pro (de pago).
- Enfoque principal basado en IA offline ejecutable desde almacenamiento físico.
- Inspiración en concepto “prepper”: guardar modelos de IA y conocimiento en pendrive.
- Integración de Wikipedia offline y paquetes de conocimiento.
- Uso de RAG offline para reducir alucinaciones.
- Diseño visual estilo programa militar retro (verde neón sobre negro).
- Uso de Vibe Coding para generar estructura base.
- Finalización técnica en Cursor.
- Arquitectura separada de carpetas para cada versión.
- Plan de monetización mediante versión Pro.
- Necesidad de fiabilidad de almacenamiento y verificación de integridad.

## 💡 4. Ideas principales y conclusiones

### Enfoque conceptual
La app se posiciona como una “Cápsula de Conocimiento Off-grid”, combinando:
- Modelos de lenguaje ejecutables localmente.
- Wikipedia offline.
- Mapas offline.
- Manuales técnicos y guías.
- Sistema de consulta con evidencias.

### Diferenciación Demo vs Pro

**Demo**
- Modelo pequeño preinstalado.
- 1 región de mapas.
- 50k artículos de Wikipedia.
- 5 checklists + 10 guías.
- SOS básico.
- Sin sincronización.

**Pro**
- Gestor de modelos (múltiples tamaños).
- Gestor de paquetes (Wikipedia completa, mapas múltiples).
- RAG avanzado con citas y nivel de confianza.
- Constructor de pendrive (verificación SHA-256).
- Inventario inteligente.
- Comunidad offline.
- Paywall simulado inicialmente.

### Infraestructura técnica propuesta
- React Native + Expo (Android/iOS + PWA).
- SQLite local.
- llama.cpp / MLC para IA offline.
- ZIM (Wikipedia offline).
- MapLibre para mapas offline.
- RevenueCat/Stripe para pagos.
- JSON mock inicial para Vibe Coding.

### Flujo de trabajo
1. Generar estructura visual en Vibe Coding.
2. Exportar repositorios separados.
3. Implementar lógica real en Cursor.
4. Integrar IA offline y RAG.
5. Añadir monetización.

### Limitaciones detectadas
- Alucinaciones en modelos pequeños.
- Fiabilidad limitada de pendrives tradicionales.
- Necesidad de verificación de integridad periódica.
- Dependencia del hardware del usuario.

## 📚 5. Recursos y ejemplos compartidos

- Concepto basado en artículo sobre IA en pendrive (MIT Technology Review).
- Modelos mencionados: Qwen 3, DeepSeek, Llama 3.2.
- Tecnologías: React Native, Expo, SQLite, llama.cpp, MapLibre.
- Uso de archivos JSON locales para MVP.
- Prompts estructurados para Vibe Coding (Demo y Pro).
- Estrategia de verificación SHA-256 y paridad opcional.

## ❓ 6. Preguntas pendientes o acciones sugeridas

- Definir tamaño mínimo de modelo objetivo (XS/S/M).
- Seleccionar primer paquete de conocimiento inicial.
- Decidir modelo de monetización (suscripción vs compra única).
- Confirmar región inicial de mapas offline.
- Establecer estructura definitiva de repositorios.
- Evaluar hardware mínimo soportado.

## 📝 7. Notas adicionales

- Estética definida como software militar retro estilo consola táctica.
- Separación clara entre versión demostrativa y versión escalable.
- Proyecto alineado con filosofía prepper tecnológica.
