# La base real: lo que se le ha hecho (23-oct-2026)

**Este documento manda sobre los resumenes anteriores.** **Los hitos se cuentan aqui, no en una copia.**

## Antes

```
F:\OpoFuente\datos\opofuente.sqlite3
  esquema 0039 · 11.315 explicaciones (todas de material privado antiguo)
  0 tarjetas · 0 supuestos · 0 planes
  huella A0A21413F6AB…  (intacta desde el 15 de octubre: "cero escrituras")
```

**Y eso era el fallo**: **la regla de la fase era que el contenido se genera sobre la base real**, **con una
copia verificada antes**, **y durante trescientas rondas se trabajo solo sobre copias**.

## Lo que se ha hecho, y cada paso con su comprobacion

| Paso | Hecho | Comprobado |
|---|---|---|
| 1 · huella de partida | `A0A21413F6AB…` | coincide con la de la que salio `m0-capturas` |
| 2 · copia verificada | `20261023-103904-fc0160` | 4.189,8 MB · 18.038 ficheros · **restaurable: True** |
| 3 · migraciones 0040→0046 | aplicadas | `alembic_version = 0046_invitaciones` |
| 4 · lo generado de verdad | 1.609 explicaciones + 9 tarjetas | 0 huerfanas · esquemas identicos (11 y 13 columnas) |
| 5 · nada de los recorridos | — | el importador solo lee esas dos tablas |
| 6 · recuentos | real = copia | explicaciones 1609 = 1609 · tarjetas 9 = 9 |
| 7 · lo que arranca el propietario | apunta a la real | `OPOFUENTE_DATA_DIR` de usuario = `F:\OpoFuente\datos` |

## Donde esta ahora la base real

```
esquema            0046_invitaciones
explicaciones      12.924   (11.315 antiguas + 1.609 generadas, estas en borrador)
tarjetas                9
supuestos               0   ← se generan de nuevo aqui (§2.4), no se copiaron
la app              /api/v1/student/progress 200 · /api/v1/stats 200
```

## Lo que no se paso, y por que

**Los 3 supuestos de la copia no viajan.** **Sus 75 preguntas y sus tres conjuntos se crearon en la copia**, **y
se generaron sobre cinco epigrafes con apuntes que la real no tiene** —**la real tiene 16 epigrafes de III y IV con
apuntes, la copia 21**—. **El plan lo dice**: **solo se pasan si salieron de apuntes de la base real**; **si no, se
generan de nuevo alli**, **que es el §2.4**.

## `notes verify --all` sobre la real

**Sale 1** —**el tema 8 no pasa la revision de forma** (una tabla sin cabecera utilizable, 24.176 palabras de
33.160)—. **Y no lo ha roto este trabajo**: **la copia tambien sale 1**, **en otro tema** (`IV.1.2`, uno de los
apuntes que escribi alli). **El importador no toca `topic_note_sections`.**

## Y lo que queda por delante

```
§2.5  el OCR            restaurar tesseract y bajar los 3 PDF de 2018
§2.2  M1                la corrida completa hasta el 100 % de las oficiales
§2.6  la bandeja        por debajo de 100, resolviendo lo automatizable
§2.3  M3                tarjetas en los 33 temas
§2.4  M5                supuestos sobre la base real
§2.7  M6 y M4           rendimiento < 2 s · por que el plan cubre 28 temas y no 33
```
