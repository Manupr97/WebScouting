def obtener_aspectos_evaluacion_completa(posicion):
    """
    Devuelve los aspectos de evaluación específicos para cada posición
    en el modo de evaluación completa (más detallado que el modo campo)
    """
    
    aspectos_por_posicion = {
        'Portero': {
            'tecnicos': {
                'Paradas reflejos': 5,
                'Blocaje seguro': 5,
                'Juego con pies': 5,
                'Saques precisión': 5,
                'Salidas aéreas': 5,
                'Mano a mano': 5
            },
            'tacticos': {
                'Posicionamiento': 5,
                'Lectura del juego': 5,
                'Comunicación defensa': 5,
                'Dominio del área': 5,
                'Anticipación': 5,
                'Organización defensiva': 5
            },
            'fisicos': {
                'Agilidad': 5,
                'Explosividad': 5,
                'Flexibilidad': 5,
                'Alcance': 5
            },
            'mentales': {
                'Concentración': 5,
                'Confianza': 5,
                'Presión': 5,
                'Recuperación errores': 5,
                'Liderazgo': 5,
                'Personalidad': 5
            }
        },
        
        'Central': {
            'tecnicos': {
                'Juego aéreo': 5,
                'Pase largo': 5,
                'Control orientado': 5,
                'Salida balón': 5,
                'Entrada limpia': 5,
                'Despeje orientado': 5
            },
            'tacticos': {
                'Marcaje hombre': 5,
                'Marcaje zonal': 5,
                'Cobertura': 5,
                'Línea de pase': 5,
                'Anticipación': 5,
                'Timing subida': 5
            },
            'fisicos': {
                'Fuerza': 5,
                'Salto': 5,
                'Velocidad': 5,
                'Resistencia': 5
            },
            'mentales': {
                'Concentración': 5,
                'Agresividad': 5,
                'Liderazgo': 5,
                'Comunicación': 5,
                'Temple': 5,
                'Inteligencia': 5
            }
        },
        
        'Lateral Derecho': {
            'tecnicos': {
                'Centro precisión': 5,
                'Control velocidad': 5,
                'Pase interior': 5,
                'Conducción': 5,
                'Tackle': 5,
                'Técnica defensiva': 5
            },
            'tacticos': {
                'Subida ataque': 5,
                'Repliegue': 5,
                'Apoyo interior': 5,
                'Vigilancia extremo': 5,
                'Basculación': 5,
                'Profundidad': 5
            },
            'fisicos': {
                'Velocidad': 5,
                'Resistencia': 5,
                'Agilidad': 5,
                'Potencia': 5
            },
            'mentales': {
                'Disciplina táctica': 5,
                'Concentración': 5,
                'Valentía': 5,
                'Inteligencia': 5,
                'Sacrificio': 5,
                'Ambición': 5
            }
        },
        
        'Lateral Izquierdo': {
            'tecnicos': {
                'Centro precisión': 5,
                'Control velocidad': 5,
                'Pase interior': 5,
                'Conducción': 5,
                'Tackle': 5,
                'Técnica defensiva': 5
            },
            'tacticos': {
                'Subida ataque': 5,
                'Repliegue': 5,
                'Apoyo interior': 5,
                'Vigilancia extremo': 5,
                'Basculación': 5,
                'Profundidad': 5
            },
            'fisicos': {
                'Velocidad': 5,
                'Resistencia': 5,
                'Agilidad': 5,
                'Potencia': 5
            },
            'mentales': {
                'Disciplina táctica': 5,
                'Concentración': 5,
                'Valentía': 5,
                'Inteligencia': 5,
                'Sacrificio': 5,
                'Ambición': 5
            }
        },
        
        'Mediocentro Defensivo': {
            'tecnicos': {
                'Interceptación': 5,
                'Pase corto seguro': 5,
                'Pase largo': 5,
                'Control presión': 5,
                'Barrido': 5,
                'Juego aéreo': 5
            },
            'tacticos': {
                'Cobertura defensiva': 5,
                'Distribución': 5,
                'Posicionamiento': 5,
                'Pressing': 5,
                'Transición def-atq': 5,
                'Lectura juego': 5
            },
            'fisicos': {
                'Resistencia': 5,
                'Fuerza': 5,
                'Agilidad': 5,
                'Potencia': 5
            },
            'mentales': {
                'Concentración': 5,
                'Disciplina': 5,
                'Liderazgo': 5,
                'Sacrificio': 5,
                'Inteligencia táctica': 5,
                'Madurez': 5
            }
        },
        
        'Mediocentro': {
            'tecnicos': {
                'Pase corto': 5,
                'Pase medio': 5,
                'Control orientado': 5,
                'Conducción': 5,
                'Tiro medio': 5,
                'Presión': 5
            },
            'tacticos': {
                'Visión juego': 5,
                'Movilidad': 5,
                'Creación espacios': 5,
                'Pressing inteligente': 5,
                'Llegada área': 5,
                'Equilibrio': 5
            },
            'fisicos': {
                'Resistencia': 5,
                'Velocidad': 5,
                'Agilidad': 5,
                'Cambio ritmo': 5
            },
            'mentales': {
                'Creatividad': 5,
                'Personalidad': 5,
                'Presión': 5,
                'Inteligencia': 5,
                'Ambición': 5,
                'Trabajo equipo': 5
            }
        },
        
        'Media Punta': {
            'tecnicos': {
                'Último pase': 5,
                'Control espacios reducidos': 5,
                'Regate corto': 5,
                'Tiro': 5,
                'Pase entre líneas': 5,
                'Técnica depurada': 5
            },
            'tacticos': {
                'Encontrar espacios': 5,
                'Asociación': 5,
                'Desmarque apoyo': 5,
                'Lectura defensiva rival': 5,
                'Timing pase': 5,
                'Cambio orientación': 5
            },
            'fisicos': {
                'Agilidad': 5,
                'Cambio ritmo': 5,
                'Equilibrio': 5,
                'Coordinación': 5
            },
            'mentales': {
                'Creatividad': 5,
                'Visión': 5,
                'Confianza': 5,
                'Personalidad': 5,
                'Presión': 5,
                'Liderazgo técnico': 5
            }
        },
        
        'Extremo Derecho': {
            'tecnicos': {
                'Regate': 5,
                'Centro': 5,
                'Finalización': 5,
                'Control velocidad': 5,
                'Cambio ritmo': 5,
                'Recorte interior': 5
            },
            'tacticos': {
                'Desmarque': 5,
                'Profundidad': 5,
                'Ayuda defensiva': 5,
                'Movimientos sin balón': 5,
                'Asociación': 5,
                'Amplitud': 5
            },
            'fisicos': {
                'Velocidad punta': 5,
                'Explosividad': 5,
                'Agilidad': 5,
                'Resistencia': 5
            },
            'mentales': {
                'Valentía 1v1': 5,
                'Confianza': 5,
                'Sacrificio': 5,
                'Perseverancia': 5,
                'Decisión': 5,
                'Ambición': 5
            }
        },
        
        'Extremo Izquierdo': {
            'tecnicos': {
                'Regate': 5,
                'Centro': 5,
                'Finalización': 5,
                'Control velocidad': 5,
                'Cambio ritmo': 5,
                'Recorte interior': 5
            },
            'tacticos': {
                'Desmarque': 5,
                'Profundidad': 5,
                'Ayuda defensiva': 5,
                'Movimientos sin balón': 5,
                'Asociación': 5,
                'Amplitud': 5
            },
            'fisicos': {
                'Velocidad punta': 5,
                'Explosividad': 5,
                'Agilidad': 5,
                'Resistencia': 5
            },
            'mentales': {
                'Valentía 1v1': 5,
                'Confianza': 5,
                'Sacrificio': 5,
                'Perseverancia': 5,
                'Decisión': 5,
                'Ambición': 5
            }
        },
        
        'Delantero': {
            'tecnicos': {
                'Finalización pie derecho': 5,
                'Finalización pie izquierdo': 5,
                'Finalización cabeza': 5,
                'Control área': 5,
                'Juego espaldas': 5,
                'Primer toque': 5
            },
            'tacticos': {
                'Desmarque ruptura': 5,
                'Timing llegada': 5,
                'Arrastre marcas': 5,
                'Pressing': 5,
                'Asociación': 5,
                'Lectura juego': 5
            },
            'fisicos': {
                'Potencia': 5,
                'Velocidad': 5,
                'Salto': 5,
                'Fuerza': 5
            },
            'mentales': {
                'Sangre fría': 5,
                'Confianza': 5,
                'Ambición': 5,
                'Persistencia': 5,
                'Competitividad': 5,
                'Presión gol': 5
            }
        }
    }
    
    # Si la posición no está definida, usar aspectos genéricos de Mediocentro
    return aspectos_por_posicion.get(posicion, aspectos_por_posicion['Mediocentro'])