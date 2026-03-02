# 📋 Análisis de Error 404 en Ejecución de Endpoint

## 🎯 2. Objetivo de la conversación

Analizar y diagnosticar un error `404` recibido durante la ejecución de
un comando relacionado con un agente (`openclaw-tui`) que intentaba
acceder a un endpoint asociado a un modelo (`opencode/glm-5-free`).

## 📌 3. Puntos clave tratados

-   Aparición de error `run error: 404`
-   Respuesta HTML en lugar de respuesta JSON esperada
-   Posible llamada a URL incorrecta
-   Diferencia entre frontend y backend
-   Revisión de infraestructura potencial:
    -   Docker
    -   Portainer
    -   Nginx Proxy Manager
-   Posibles causas técnicas:
    -   Endpoint inexistente
    -   Contenedor no levantado
    -   Proxy mal configurado
    -   Modelo mal especificado
    -   API base URL incorrecta
    -   Token/API Key inválida

## 💡 4. Ideas principales y conclusiones

### Interpretación del Error

Un error 404 indica que el recurso solicitado no existe en la ruta
especificada.

El hecho de recibir HTML (`<!DOCTYPE html>`) sugiere que: - Se está
llamando a una página web (frontend) - No se está alcanzando el endpoint
de backend esperado

### Causas Técnicas Probables

1.  URL incorrecta o mal escrita.
2.  Ruta `/api/...` no definida en el backend.
3.  Proxy (Nginx) redirigiendo al `index.html`.
4.  Contenedor Docker detenido o puerto no expuesto.
5.  Modelo o endpoint mal configurado en el cliente TUI.

### Diagnóstico Recomendado

-   Verificar endpoint con `curl -I`
-   Revisar contenedores en Portainer
-   Confirmar mapeo de puertos
-   Validar configuración del proxy
-   Revisar API base URL y credenciales

### Lección Técnica

Cuando una API devuelve HTML en vez de JSON, normalmente: - Se está
tocando el frontend - El backend no está accesible - Existe mala
configuración en proxy o ruta

## 📚 5. Recursos y ejemplos compartidos

-   Uso de `curl` para diagnóstico:
    -   `curl -I https://tu-endpoint.com/api`
    -   `curl https://tu-endpoint.com/api`
-   Infraestructura mencionada:
    -   Docker
    -   Portainer
    -   Nginx Proxy Manager
-   Cliente implicado:
    -   openclaw-tui
-   Modelo mencionado:
    -   opencode/glm-5-free

## ❓ 6. Preguntas pendientes o acciones sugeridas

-   Confirmar URL exacta utilizada.
-   Verificar si el backend está activo.
-   Confirmar que el endpoint existe.
-   Revisar configuración de proxy inverso.
-   Validar credenciales/API key.
-   Confirmar entorno (local vs producción).

## 📝 7. Notas adicionales

El error no parece estar relacionado con el modelo en sí, sino con la
conectividad o configuración de red entre cliente y backend.
