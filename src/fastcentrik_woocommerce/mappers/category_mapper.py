#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WooCommerce Category Mapper
===========================

Inteligentní mapování produktů do správných WooCommerce kategorií
na základě atributů produktu, názvu a dalších parametrů.

Autor: FastCentrik Migration Tool
Verze: 1.0
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

logger = logging.getLogger(__name__)


class CategoryMapper:
    """
    Mapuje produkty do WooCommerce kategorií na základě definovaných pravidel.
    """
    
    def __init__(self):
        """Inicializace mapperu s definicí kategoriální struktury."""
        self.category_structure = self._define_category_structure()
        self.mapping_stats = {
            'mapped': 0,
            'fallback': 0,
            'unmapped': 0,
            'category_counts': {}
        }
        
    def _define_category_structure(self) -> Dict:
        """
        Definuje kompletní strukturu WooCommerce kategorií s pravidly pro mapování.
        
        Struktura pravidel:
        - name_contains: seznam slov, která musí obsahovat název produktu
        - name_regex: regulární výraz pro název produktu
        - params: slovník parametrů a jejich hodnot
        - params_any: alespoň jeden z parametrů musí odpovídat
        - brand_contains: značka obsahuje
        - priority: priorita pravidla (vyšší = důležitější)
        """
        return {
            "Muži": {
                "conditions": [
                    {"params": {"pohlavi": ["pánské", "muž", "men"]}},
                    {"name_contains": ["pánsk", "muž", "men's"]},
                    {"params": {"kategorie": ["pánské"]}}
                ],
                "subcategories": {
                    "Pánské oblečení": {
                        "conditions": [
                            {"name_contains": ["oblečení", "mikina", "kalhoty", "tričko", "bunda", "kabát"]},
                            {"params": {"typ": ["oblečení", "oděv"]}}
                        ],
                        "subcategories": {
                            "Pánské mikiny": {
                                "conditions": [
                                    {"name_contains": ["mikina", "hoodie", "sweatshirt"]},
                                    {"params": {"typ": ["mikina"]}}
                                ],
                                "priority": 10
                            },
                            "Pánské kalhoty": {
                                "conditions": [
                                    {"name_contains": ["kalhoty", "džíny", "jeans", "tepláky", "kraťasy", "shorts"]},
                                    {"params": {"typ": ["kalhoty", "džíny", "tepláky"]}}
                                ],
                                "priority": 10
                            },
                            "Pánská trička": {
                                "conditions": [
                                    {"name_contains": ["tričko", "triko", "t-shirt", "tshirt", "polo"]},
                                    {"params": {"typ": ["tričko", "triko"]}}
                                ],
                                "priority": 10
                            },
                            "Pánské zimní oblečení": {
                                "conditions": [
                                    {"name_contains": ["zimní", "bunda", "kabát", "parka", "péřov", "lyžařsk"]},
                                    {"params": {"sezona": ["zima", "zimní"]}},
                                    {"params": {"typ": ["bunda", "kabát", "zimní oblečení"]}}
                                ],
                                "priority": 9
                            }
                        }
                    },
                    "Pánské boty": {
                        "conditions": [
                            {"name_contains": ["boty", "tenisky", "obuv", "kopačky", "tretry", "pantofle", "sandále"]},
                            {"params": {"typ": ["obuv", "boty"]}}
                        ],
                        "subcategories": {
                            "Pánská outdoorová obuv": {
                                "conditions": [
                                    {"name_contains": ["outdoor", "trekk", "trek", "hory", "turistick"]},
                                    {"params": {"typ": ["outdoor obuv", "trekové boty"]}}
                                ],
                                "priority": 10
                            },
                            "Pánské tenisky": {
                                "conditions": [
                                    {"name_contains": ["tenisky", "sneaker", "lifestyle", "volnočas"]},
                                    {"params": {"typ": ["tenisky", "sneakers"]}}
                                ],
                                "priority": 10
                            },
                            "Pánské pantofle": {
                                "conditions": [
                                    {"name_contains": ["pantofle", "nazouváky", "přezůvky", "domácí obuv"]},
                                    {"params": {"typ": ["pantofle"]}}
                                ],
                                "priority": 10
                            },
                            "Pánské sandále": {
                                "conditions": [
                                    {"name_contains": ["sandále", "sandály", "žabky"]},
                                    {"params": {"typ": ["sandále"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Pánské doplňky": {
                        "conditions": [
                            {"name_contains": ["batoh", "čepice", "rukavice", "šála", "pásek", "peněženka"]},
                            {"params": {"typ": ["doplňky", "příslušenství"]}}
                        ],
                        "subcategories": {
                            "Pánské batohy": {
                                "conditions": [
                                    {"name_contains": ["batoh", "ruksak", "backpack"]},
                                    {"params": {"typ": ["batoh"]}}
                                ],
                                "priority": 10
                            },
                            "Pánské čepice": {
                                "conditions": [
                                    {"name_contains": ["čepice", "kšiltovka", "kulich", "cap", "beanie"]},
                                    {"params": {"typ": ["čepice", "pokrývka hlavy"]}}
                                ],
                                "priority": 10
                            }
                        }
                    }
                }
            },
            "Ženy": {
                "conditions": [
                    {"params": {"pohlavi": ["dámské", "žena", "women"]}},
                    {"name_contains": ["dámsk", "žen", "women's"]},
                    {"params": {"kategorie": ["dámské"]}}
                ],
                "subcategories": {
                    "Dámské oblečení": {
                        "conditions": [
                            {"name_contains": ["oblečení", "mikina", "kalhoty", "tričko", "šaty", "sukně"]},
                            {"params": {"typ": ["oblečení", "oděv"]}}
                        ],
                        "subcategories": {
                            "Dámské mikiny": {
                                "conditions": [
                                    {"name_contains": ["mikina", "hoodie", "sweatshirt"]},
                                    {"params": {"typ": ["mikina"]}}
                                ],
                                "priority": 10
                            },
                            "Dámská trička": {
                                "conditions": [
                                    {"name_contains": ["tričko", "triko", "t-shirt", "tshirt", "top"]},
                                    {"params": {"typ": ["tričko", "triko", "top"]}}
                                ],
                                "priority": 10
                            },
                            "Dámské kalhoty": {
                                "conditions": [
                                    {"name_contains": ["kalhoty", "džíny", "jeans", "legíny", "leggings"]},
                                    {"params": {"typ": ["kalhoty", "džíny", "legíny"]}}
                                ],
                                "priority": 10
                            },
                            "Dámské zimní oblečení": {
                                "conditions": [
                                    {"name_contains": ["zimní", "bunda", "kabát", "parka", "péřov"]},
                                    {"params": {"sezona": ["zima", "zimní"]}},
                                    {"params": {"typ": ["bunda", "kabát", "zimní oblečení"]}}
                                ],
                                "priority": 9
                            }
                        }
                    },
                    "Dámské boty": {
                        "conditions": [
                            {"name_contains": ["boty", "tenisky", "obuv", "lodičky", "kozačky", "pantofle"]},
                            {"params": {"typ": ["obuv", "boty"]}}
                        ],
                        "subcategories": {
                            "Dámská outdoorová obuv": {
                                "conditions": [
                                    {"name_contains": ["outdoor", "trekk", "trek", "turistick"]},
                                    {"params": {"typ": ["outdoor obuv", "trekové boty"]}}
                                ],
                                "priority": 10
                            },
                            "Dámské tenisky": {
                                "conditions": [
                                    {"name_contains": ["tenisky", "sneaker", "lifestyle"]},
                                    {"params": {"typ": ["tenisky", "sneakers"]}}
                                ],
                                "priority": 10
                            },
                            "Dámské pantofle": {
                                "conditions": [
                                    {"name_contains": ["pantofle", "nazouváky", "přezůvky"]},
                                    {"params": {"typ": ["pantofle"]}}
                                ],
                                "priority": 10
                            },
                            "Dámské sandále": {
                                "conditions": [
                                    {"name_contains": ["sandále", "sandály", "žabky"]},
                                    {"params": {"typ": ["sandále"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Dámské doplňky": {
                        "conditions": [
                            {"name_contains": ["batoh", "čepice", "kabelka", "šála", "rukavice"]},
                            {"params": {"typ": ["doplňky", "příslušenství"]}}
                        ],
                        "subcategories": {
                            "Dámské batohy": {
                                "conditions": [
                                    {"name_contains": ["batoh", "ruksak", "backpack"]},
                                    {"params": {"typ": ["batoh"]}}
                                ],
                                "priority": 10
                            },
                            "Dámské čepice": {
                                "conditions": [
                                    {"name_contains": ["čepice", "kšiltovka", "kulich", "baret"]},
                                    {"params": {"typ": ["čepice", "pokrývka hlavy"]}}
                                ],
                                "priority": 10
                            }
                        }
                    }
                }
            },
            "Děti": {
                "conditions": [
                    {"params": {"pohlavi": ["dětské", "děti", "kids", "junior"]}},
                    {"name_contains": ["dětsk", "junior", "kids", "boy", "girl"]},
                    {"params": {"kategorie": ["dětské"]}}
                ],
                "subcategories": {
                    "Dětské oblečení": {
                        "conditions": [
                            {"name_contains": ["oblečení", "mikina", "kalhoty", "tričko"]},
                            {"params": {"typ": ["oblečení", "oděv"]}}
                        ],
                        "subcategories": {
                            "Dětské mikiny": {
                                "conditions": [
                                    {"name_contains": ["mikina", "hoodie", "sweatshirt"]},
                                    {"params": {"typ": ["mikina"]}}
                                ],
                                "priority": 10
                            },
                            "Dětská trička": {
                                "conditions": [
                                    {"name_contains": ["tričko", "triko", "t-shirt"]},
                                    {"params": {"typ": ["tričko", "triko"]}}
                                ],
                                "priority": 10
                            },
                            "Dětské kalhoty": {
                                "conditions": [
                                    {"name_contains": ["kalhoty", "džíny", "tepláky", "kraťasy"]},
                                    {"params": {"typ": ["kalhoty", "džíny", "tepláky"]}}
                                ],
                                "priority": 10
                            },
                            "Dětské zimní oblečení": {
                                "conditions": [
                                    {"name_contains": ["zimní", "bunda", "kombinéza", "lyžařsk"]},
                                    {"params": {"sezona": ["zima", "zimní"]}},
                                    {"params": {"typ": ["bunda", "zimní oblečení"]}}
                                ],
                                "priority": 9
                            }
                        }
                    },
                    "Dětské boty": {
                        "conditions": [
                            {"name_contains": ["boty", "tenisky", "obuv", "sandále"]},
                            {"params": {"typ": ["obuv", "boty"]}}
                        ],
                        "subcategories": {
                            "Dětské outdoorové boty": {
                                "conditions": [
                                    {"name_contains": ["outdoor", "turistick", "trek"]},
                                    {"params": {"typ": ["outdoor obuv"]}}
                                ],
                                "priority": 10
                            },
                            "Dětské tenisky": {
                                "conditions": [
                                    {"name_contains": ["tenisky", "sneaker"]},
                                    {"params": {"typ": ["tenisky", "sneakers"]}}
                                ],
                                "priority": 10
                            },
                            "Dětské pantofle": {
                                "conditions": [
                                    {"name_contains": ["pantofle", "přezůvky"]},
                                    {"params": {"typ": ["pantofle"]}}
                                ],
                                "priority": 10
                            },
                            "Dětské sandále": {
                                "conditions": [
                                    {"name_contains": ["sandále", "sandály"]},
                                    {"params": {"typ": ["sandále"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Dětské doplňky": {
                        "conditions": [
                            {"name_contains": ["batoh", "čepice", "rukavice"]},
                            {"params": {"typ": ["doplňky", "příslušenství"]}}
                        ],
                        "subcategories": {
                            "Dětské batohy": {
                                "conditions": [
                                    {"name_contains": ["batoh", "školní batoh"]},
                                    {"params": {"typ": ["batoh"]}}
                                ],
                                "priority": 10
                            },
                            "Dětské čepice": {
                                "conditions": [
                                    {"name_contains": ["čepice", "kulich", "kšiltovka"]},
                                    {"params": {"typ": ["čepice"]}}
                                ],
                                "priority": 10
                            }
                        }
                    }
                }
            },
            "Sporty": {
                "conditions": [
                    {"params": {"sport": ["fotbal", "tenis", "basketbal", "běh", "fitness", "hokej"]}},
                    {"name_contains": ["sport", "fotbal", "tenis", "basketbal", "běh", "fitness"]},
                    {"params": {"kategorie": ["sport", "sporty"]}}
                ],
                "subcategories": {
                    "Fotbal": {
                        "conditions": [
                            {"params": {"sport": ["fotbal", "football", "soccer"]}},
                            {"name_contains": ["fotbal", "kopačky", "football", "soccer"]},
                            {"params": {"typ": ["kopačky", "fotbalové vybavení"]}}
                        ],
                        "subcategories": {
                            "Kopačky": {
                                "conditions": [
                                    {"name_contains": ["kopačky", "kopačka"]},
                                    {"params": {"typ": ["kopačky"]}}
                                ],
                                "subcategories": {
                                    "Lisovky": {
                                        "conditions": [
                                            {"name_contains": ["lisovky", "FG", "AG"]},
                                            {"params": {"povrch": ["FG", "AG", "lisovky"]}}
                                        ],
                                        "priority": 12
                                    },
                                    "Kolíky a lisokolíky": {
                                        "conditions": [
                                            {"name_contains": ["kolíky", "SG", "lisokolíky"]},
                                            {"params": {"povrch": ["SG", "kolíky"]}}
                                        ],
                                        "priority": 12
                                    },
                                    "Sálovky": {
                                        "conditions": [
                                            {"name_contains": ["sálovky", "IC", "IN", "indoor"]},
                                            {"params": {"povrch": ["IC", "IN", "sálovky"]}}
                                        ],
                                        "priority": 12
                                    },
                                    "Turfy": {
                                        "conditions": [
                                            {"name_contains": ["turfy", "TF", "turf"]},
                                            {"params": {"povrch": ["TF", "turfy"]}}
                                        ],
                                        "priority": 12
                                    }
                                }
                            },
                            "Fotbalové míče": {
                                "conditions": [
                                    {"name_contains": ["míč", "ball", "fotbalový míč"]},
                                    {"params": {"typ": ["míč", "fotbalový míč"]}}
                                ],
                                "priority": 10
                            },
                            "Fotbalové oblečení": {
                                "conditions": [
                                    {"name_contains": ["dres", "trenýrky", "štulpny", "fotbalové oblečení"]},
                                    {"params": {"typ": ["dres", "fotbalové oblečení"]}}
                                ],
                                "priority": 10
                            },
                            "Fotbalový brankář": {
                                "conditions": [
                                    {"name_contains": ["brankář", "rukavice", "goalkeeper"]},
                                    {"params": {"typ": ["brankářské vybavení"]}}
                                ],
                                "priority": 10
                            },
                            "Fotbalové chrániče": {
                                "conditions": [
                                    {"name_contains": ["chránič", "chrániče", "shin"]},
                                    {"params": {"typ": ["chrániče"]}}
                                ],
                                "priority": 10
                            },
                            "Fotbalové vybavení": {
                                "conditions": [
                                    {"name_contains": ["trénink", "kužel", "meta", "síť"]},
                                    {"params": {"typ": ["tréninkové vybavení"]}}
                                ],
                                "priority": 9
                            }
                        }
                    },
                    "Tenis": {
                        "conditions": [
                            {"params": {"sport": ["tenis", "tennis"]}},
                            {"name_contains": ["tenis", "tennis", "raketa"]},
                            {"params": {"typ": ["tenisové vybavení"]}}
                        ],
                        "subcategories": {
                            "Tenisové rakety": {
                                "conditions": [
                                    {"name_contains": ["raketa", "racket", "racquet"]},
                                    {"params": {"typ": ["raketa", "tenisová raketa"]}}
                                ],
                                "priority": 10
                            },
                            "Tenisové boty": {
                                "conditions": [
                                    {"name_contains": ["tenisové boty", "tennis shoes"]},
                                    {"params": {"typ": ["tenisové boty"]}}
                                ],
                                "priority": 10
                            },
                            "Tenisové míče a doplňky": {
                                "conditions": [
                                    {"name_contains": ["tenisový míč", "tennis ball", "výplet", "grip"]},
                                    {"params": {"typ": ["tenisové míče", "tenisové doplňky"]}}
                                ],
                                "priority": 10
                            },
                            "Tenisové tašky": {
                                "conditions": [
                                    {"name_contains": ["tenisová taška", "tennis bag"]},
                                    {"params": {"typ": ["tenisová taška"]}}
                                ],
                                "priority": 10
                            },
                            "Tenisové oblečení": {
                                "conditions": [
                                    {"name_contains": ["tenisové oblečení", "tennis wear"]},
                                    {"params": {"typ": ["tenisové oblečení"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Padel": {
                        "conditions": [
                            {"params": {"sport": ["padel"]}},
                            {"name_contains": ["padel"]},
                            {"params": {"typ": ["padelové vybavení"]}}
                        ],
                        "subcategories": {
                            "Padelové rakety": {
                                "conditions": [
                                    {"name_contains": ["padelová raketa", "padel racket"]},
                                    {"params": {"typ": ["padelová raketa"]}}
                                ],
                                "priority": 10
                            },
                            "Padelové míče a doplňky": {
                                "conditions": [
                                    {"name_contains": ["padelový míč", "padel ball"]},
                                    {"params": {"typ": ["padelové míče", "padelové doplňky"]}}
                                ],
                                "priority": 10
                            },
                            "Padelové tašky": {
                                "conditions": [
                                    {"name_contains": ["padelová taška", "padel bag"]},
                                    {"params": {"typ": ["padelová taška"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Basketbal": {
                        "conditions": [
                            {"params": {"sport": ["basketbal", "basketball"]}},
                            {"name_contains": ["basketbal", "basketball"]},
                            {"params": {"typ": ["basketbalové vybavení"]}}
                        ],
                        "subcategories": {
                            "Basketbalové boty": {
                                "conditions": [
                                    {"name_contains": ["basketbalové boty", "basketball shoes"]},
                                    {"params": {"typ": ["basketbalové boty"]}}
                                ],
                                "priority": 10
                            },
                            "Basketbalové míče": {
                                "conditions": [
                                    {"name_contains": ["basketbalový míč", "basketball"]},
                                    {"params": {"typ": ["basketbalový míč"]}}
                                ],
                                "priority": 10
                            },
                            "Basketbalové oblečení": {
                                "conditions": [
                                    {"name_contains": ["basketbalový dres", "basketball jersey"]},
                                    {"params": {"typ": ["basketbalové oblečení"]}}
                                ],
                                "priority": 10
                            },
                            "Basketbalové desky a koše": {
                                "conditions": [
                                    {"name_contains": ["basketbalový koš", "deska", "hoop"]},
                                    {"params": {"typ": ["basketbalový koš", "basketbalová deska"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Bojové sporty": {
                        "conditions": [
                            {"params": {"sport": ["box", "mma", "karate", "judo", "bojové sporty"]}},
                            {"name_contains": ["box", "mma", "karate", "judo", "bojov"]},
                            {"params": {"typ": ["bojové vybavení"]}}
                        ],
                        "subcategories": {
                            "Box": {
                                "conditions": [
                                    {"params": {"sport": ["box", "boxing"]}},
                                    {"name_contains": ["box", "boxing", "boxersk"]},
                                    {"params": {"typ": ["boxerské vybavení"]}}
                                ],
                                "priority": 10
                            },
                            "MMA": {
                                "conditions": [
                                    {"params": {"sport": ["mma"]}},
                                    {"name_contains": ["mma", "mixed martial"]},
                                    {"params": {"typ": ["mma vybavení"]}}
                                ],
                                "priority": 10
                            },
                            "Karate": {
                                "conditions": [
                                    {"params": {"sport": ["karate"]}},
                                    {"name_contains": ["karate"]},
                                    {"params": {"typ": ["karate vybavení"]}}
                                ],
                                "priority": 10
                            },
                            "Judo": {
                                "conditions": [
                                    {"params": {"sport": ["judo"]}},
                                    {"name_contains": ["judo", "judogi"]},
                                    {"params": {"typ": ["judo vybavení"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Běh": {
                        "conditions": [
                            {"params": {"sport": ["běh", "running"]}},
                            {"name_contains": ["běh", "běžeck", "running"]},
                            {"params": {"typ": ["běžecké vybavení"]}}
                        ],
                        "subcategories": {
                            "Běžecká obuv": {
                                "conditions": [
                                    {"name_contains": ["běžecké boty", "running shoes", "běžecká obuv"]},
                                    {"params": {"typ": ["běžecké boty", "běžecká obuv"]}}
                                ],
                                "priority": 10
                            },
                            "Běžecké oblečení": {
                                "conditions": [
                                    {"name_contains": ["běžecké oblečení", "running wear"]},
                                    {"params": {"typ": ["běžecké oblečení"]}}
                                ],
                                "priority": 10
                            },
                            "Běžecké batohy": {
                                "conditions": [
                                    {"name_contains": ["běžecký batoh", "running pack"]},
                                    {"params": {"typ": ["běžecký batoh"]}}
                                ],
                                "priority": 10
                            },
                            "Běžecké doplňky": {
                                "conditions": [
                                    {"name_contains": ["běžecké doplňky", "čelovka", "pás"]},
                                    {"params": {"typ": ["běžecké doplňky"]}}
                                ],
                                "priority": 10
                            }
                        }
                    },
                    "Lední hokej": {
                        "conditions": [
                            {"params": {"sport": ["hokej", "lední hokej", "ice hockey"]}},
                            {"name_contains": ["hokej", "hockey", "brusle"]},
                            {"params": {"typ": ["hokejové vybavení"]}}
                        ],
                        "priority": 8
                    },
                    "Fitness": {
                        "conditions": [
                            {"params": {"sport": ["fitness", "posilování"]}},
                            {"name_contains": ["fitness", "posilov", "činka", "gym"]},
                            {"params": {"typ": ["fitness vybavení"]}}
                        ],
                        "subcategories": {
                            "Fitness obuv": {
                                "conditions": [
                                    {"name_contains": ["fitness boty", "gym shoes"]},
                                    {"params": {"typ": ["fitness obuv"]}}
                                ],
                                "priority": 10
                            },
                            "Stroje": {
                                "conditions": [
                                    {"name_contains": ["stroj", "běžecký pás", "rotoped"]},
                                    {"params": {"typ": ["fitness stroj", "posilovací stroj"]}}
                                ],
                                "subcategories": {
                                    "Kardio stroje": {
                                        "conditions": [
                                            {"name_contains": ["běžecký pás", "rotoped", "eliptical"]},
                                            {"params": {"typ": ["kardio stroj"]}}
                                        ],
                                        "priority": 11
                                    },
                                    "Posilovací stroje": {
                                        "conditions": [
                                            {"name_contains": ["posilovací stroj", "bench", "stojan"]},
                                            {"params": {"typ": ["posilovací stroj"]}}
                                        ],
                                        "priority": 11
                                    }
                                }
                            },
                            "Jóga": {
                                "conditions": [
                                    {"name_contains": ["jóga", "yoga"]},
                                    {"params": {"typ": ["jóga vybavení"]}}
                                ],
                                "priority": 10
                            },
                            "Pilates": {
                                "conditions": [
                                    {"name_contains": ["pilates"]},
                                    {"params": {"typ": ["pilates vybavení"]}}
                                ],
                                "priority": 10
                            },
                            "Cvičící vybavení": {
                                "conditions": [
                                    {"name_contains": ["činka", "kettlebell", "guma", "expandér"]},
                                    {"params": {"typ": ["cvičící vybavení", "fitness doplňky"]}}
                                ],
                                "priority": 9
                            }
                        }
                    }
                }
            }
        }
    
    def map_product_to_category(self, product_name: str, product_params: Dict[str, Any],
                               original_category: Optional[str] = None) -> Tuple[str, str]:
        """
        Mapuje produkt do správné WooCommerce kategorie.
        
        Args:
            product_name: Název produktu
            product_params: Slovník parametrů produktu
            original_category: Původní kategorie z FastCentriku
            
        Returns:
            Tuple[str, str]: (category_path, mapping_type)
                - category_path: Hierarchická cesta kategorie (např. "Muži > Pánské oblečení > Pánské mikiny")
                - mapping_type: Typ mapování ("exact", "fallback", "unmapped")
        """
        # Normalizace názvu produktu pro porovnávání
        product_name_lower = product_name.lower() if product_name else ""
        
        # Normalizace parametrů
        normalized_params = {}
        for key, value in product_params.items():
            if value:
                normalized_params[key.lower()] = str(value).lower()
        
        # Pokus o nalezení nejlepší shody
        best_match = self._find_best_category_match(
            product_name_lower,
            normalized_params,
            self.category_structure
        )
        
        if best_match:
            self.mapping_stats['mapped'] += 1
            self.mapping_stats['category_counts'][best_match] = \
                self.mapping_stats['category_counts'].get(best_match, 0) + 1
            return best_match, "exact"
        
        # Fallback na původní kategorii
        if original_category:
            self.mapping_stats['fallback'] += 1
            logger.warning(f"Použit fallback pro produkt '{product_name}' -> '{original_category}'")
            return original_category, "fallback"
        
        # Produkt nemohl být namapován
        self.mapping_stats['unmapped'] += 1
        logger.error(f"Produkt '{product_name}' nemohl být namapován do žádné kategorie")
        return "", "unmapped"
    
    def map_product_to_multiple_categories(self, product_name: str, product_params: Dict[str, Any],
                                         original_category: Optional[str] = None,
                                         max_categories: int = 2,
                                         strategy: str = "complementary") -> Tuple[List[str], str]:
        """
        Mapuje produkt do více WooCommerce kategorií.
        
        Args:
            product_name: Název produktu
            product_params: Slovník parametrů produktu
            original_category: Původní kategorie z FastCentriku
            max_categories: Maximální počet kategorií
            strategy: Strategie mapování ("complementary" nebo "all_matches")
                - complementary: Vybere kategorie z různých hlavních větví
                - all_matches: Vybere všechny odpovídající kategorie
            
        Returns:
            Tuple[List[str], str]: (seznam kategorií, mapping_type)
                - seznam kategorií: Seznam hierarchických cest kategorií
                - mapping_type: Typ mapování ("exact", "fallback", "unmapped")
        """
        # Normalizace názvu produktu pro porovnávání
        product_name_lower = product_name.lower() if product_name else ""
        
        # Normalizace parametrů
        normalized_params = {}
        for key, value in product_params.items():
            if value:
                normalized_params[key.lower()] = str(value).lower()
        
        # Najít všechny odpovídající kategorie
        all_matches = self._find_all_category_matches(
            product_name_lower,
            normalized_params,
            self.category_structure
        )
        
        # Aplikovat strategii výběru
        if strategy == "complementary":
            selected_categories = self._select_complementary_categories(all_matches, max_categories)
        else:  # all_matches
            selected_categories = self._select_best_matches(all_matches, max_categories)
        
        if selected_categories:
            self.mapping_stats['mapped'] += 1
            for category in selected_categories:
                self.mapping_stats['category_counts'][category] = \
                    self.mapping_stats['category_counts'].get(category, 0) + 1
            return selected_categories, "exact"
        
        # Fallback na původní kategorii
        if original_category:
            self.mapping_stats['fallback'] += 1
            logger.warning(f"Použit fallback pro produkt '{product_name}' -> '{original_category}'")
            return [original_category], "fallback"
        
        # Produkt nemohl být namapován
        self.mapping_stats['unmapped'] += 1
        logger.error(f"Produkt '{product_name}' nemohl být namapován do žádné kategorie")
        return [], "unmapped"
    
    def _find_best_category_match(self, product_name: str, params: Dict[str, str],
                                  category_tree: Dict, parent_path: str = "") -> Optional[str]:
        """
        Rekurzivně prochází strom kategorií a hledá nejlepší shodu.
        
        Args:
            product_name: Normalizovaný název produktu
            params: Normalizované parametry produktu
            category_tree: Aktuální úroveň stromu kategorií
            parent_path: Cesta k nadřazené kategorii
            
        Returns:
            Nejlepší nalezená kategorie nebo None
        """
        best_match = None
        best_priority = -1
        
        for category_name, category_data in category_tree.items():
            current_path = f"{parent_path} > {category_name}" if parent_path else category_name
            
            # Kontrola podmínek pro aktuální kategorii
            if self._check_category_conditions(product_name, params, category_data.get('conditions', [])):
                # Rekurzivní prohledávání podkategorií
                if 'subcategories' in category_data:
                    sub_match = self._find_best_category_match(
                        product_name, params,
                        category_data['subcategories'],
                        current_path
                    )
                    if sub_match:
                        # Podkategorie má vždy vyšší prioritu
                        return sub_match
                
                # Pokud nemá podkategorie nebo žádná nevyhovuje, použít tuto kategorii
                priority = category_data.get('priority', 0)
                if priority > best_priority:
                    best_match = current_path
                    best_priority = priority
        
        return best_match
    
    def _find_all_category_matches(self, product_name: str, params: Dict[str, str],
                                  category_tree: Dict, parent_path: str = "") -> List[Tuple[str, int, int]]:
        """
        Rekurzivně prochází strom kategorií a najde všechny odpovídající kategorie.
        
        Args:
            product_name: Normalizovaný název produktu
            params: Normalizované parametry produktu
            category_tree: Aktuální úroveň stromu kategorií
            parent_path: Cesta k nadřazené kategorii
            
        Returns:
            Seznam tuple (category_path, priority, depth)
        """
        matches = []
        
        for category_name, category_data in category_tree.items():
            current_path = f"{parent_path} > {category_name}" if parent_path else category_name
            current_depth = current_path.count(' > ') + 1
            
            # Kontrola podmínek pro aktuální kategorii
            if self._check_category_conditions(product_name, params, category_data.get('conditions', [])):
                priority = category_data.get('priority', 0)
                
                # Rekurzivní prohledávání podkategorií
                if 'subcategories' in category_data:
                    sub_matches = self._find_all_category_matches(
                        product_name, params,
                        category_data['subcategories'],
                        current_path
                    )
                    matches.extend(sub_matches)
                    
                    # Přidat aktuální kategorii pouze pokud nemá odpovídající podkategorie
                    if not sub_matches:
                        matches.append((current_path, priority, current_depth))
                else:
                    # Kategorie bez podkategorií
                    matches.append((current_path, priority, current_depth))
        
        return matches
    
    def _select_complementary_categories(self, matches: List[Tuple[str, int, int]],
                                       max_categories: int) -> List[str]:
        """
        Vybere komplementární kategorie z různých hlavních větví.
        
        Args:
            matches: Seznam tuple (category_path, priority, depth)
            max_categories: Maximální počet kategorií
            
        Returns:
            Seznam vybraných kategorií
        """
        if not matches:
            return []
        
        # Seskupit kategorie podle hlavní větve
        branches = {}
        for category_path, priority, depth in matches:
            main_branch = category_path.split(' > ')[0]
            if main_branch not in branches:
                branches[main_branch] = []
            branches[main_branch].append((category_path, priority, depth))
        
        # Vybrat nejlepší kategorii z každé větve
        selected = []
        for branch, branch_matches in branches.items():
            # Seřadit podle priority a hloubky (hlubší = specifičtější = lepší)
            branch_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
            if branch_matches:
                selected.append(branch_matches[0])
        
        # Seřadit všechny vybrané podle priority
        selected.sort(key=lambda x: x[1], reverse=True)
        
        # Vrátit pouze cesty kategorií, omezené na max_categories
        return [cat[0] for cat in selected[:max_categories]]
    
    def _select_best_matches(self, matches: List[Tuple[str, int, int]],
                           max_categories: int) -> List[str]:
        """
        Vybere nejlepší kategorie podle priority a specifičnosti.
        
        Args:
            matches: Seznam tuple (category_path, priority, depth)
            max_categories: Maximální počet kategorií
            
        Returns:
            Seznam vybraných kategorií
        """
        if not matches:
            return []
        
        # Seřadit podle priority a hloubky
        matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Vrátit pouze cesty kategorií, omezené na max_categories
        return [cat[0] for cat in matches[:max_categories]]
    
    def _check_category_conditions(self, product_name: str, params: Dict[str, str],
                                  conditions: List[Dict]) -> bool:
        """
        Kontroluje, zda produkt splňuje podmínky pro danou kategorii.
        
        Args:
            product_name: Normalizovaný název produktu
            params: Normalizované parametry produktu
            conditions: Seznam podmínek pro kategorii
            
        Returns:
            True pokud produkt splňuje alespoň jednu podmínku
        """
        if not conditions:
            return False
        
        for condition in conditions:
            # Kontrola názvu produktu
            if 'name_contains' in condition:
                if any(word in product_name for word in condition['name_contains']):
                    return True
            
            # Kontrola regulárního výrazu
            if 'name_regex' in condition:
                if re.search(condition['name_regex'], product_name):
                    return True
            
            # Kontrola parametrů
            if 'params' in condition:
                params_match = True
                for param_name, param_values in condition['params'].items():
                    if param_name.lower() not in params:
                        params_match = False
                        break
                    
                    param_value = params[param_name.lower()]
                    # Pokud je param_values seznam, kontrolujeme, zda hodnota je v seznamu
                    if isinstance(param_values, list):
                        if not any(v.lower() in param_value for v in param_values):
                            params_match = False
                            break
                    # Pokud je param_values string, kontrolujeme částečnou shodu
                    else:
                        if param_values.lower() not in param_value:
                            params_match = False
                            break
                
                if params_match:
                    return True
            
            # Kontrola parametrů s podmínkou "alespoň jeden"
            if 'params_any' in condition:
                for param_name, param_values in condition['params_any'].items():
                    if param_name.lower() in params:
                        param_value = params[param_name.lower()]
                        if isinstance(param_values, list):
                            if param_value in [v.lower() for v in param_values]:
                                return True
                        else:
                            if param_value == param_values.lower():
                                return True
            
            # Kontrola značky
            if 'brand_contains' in condition:
                brand = params.get('znacka', '') or params.get('vyrobce', '')
                if any(word in brand for word in condition['brand_contains']):
                    return True
        
        return False
    
    def get_mapping_stats(self) -> Dict:
        """
        Vrací statistiky mapování.
        
        Returns:
            Slovník se statistikami mapování
        """
        return self.mapping_stats
    
    def reset_stats(self):
        """Resetuje statistiky mapování."""
        self.mapping_stats = {
            'mapped': 0,
            'fallback': 0,
            'unmapped': 0,
            'category_counts': {}
        }
    
    def print_mapping_report(self):
        """Vytiskne report o mapování kategorií."""
        total = self.mapping_stats['mapped'] + self.mapping_stats['fallback'] + self.mapping_stats['unmapped']
        
        if total == 0:
            print("Žádné produkty nebyly zpracovány.")
            return
        
        print("\n" + "="*60)
        print("REPORT MAPOVÁNÍ KATEGORIÍ")
        print("="*60)
        print(f"Celkem zpracováno produktů: {total}")
        print(f"Úspěšně namapováno: {self.mapping_stats['mapped']} ({self.mapping_stats['mapped']/total*100:.1f}%)")
        print(f"Použit fallback: {self.mapping_stats['fallback']} ({self.mapping_stats['fallback']/total*100:.1f}%)")
        print(f"Nenamapováno: {self.mapping_stats['unmapped']} ({self.mapping_stats['unmapped']/total*100:.1f}%)")
        
        if self.mapping_stats['category_counts']:
            print("\nNejpoužívanější kategorie:")
            sorted_categories = sorted(
                self.mapping_stats['category_counts'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for category, count in sorted_categories[:20]:
                print(f"  {category}: {count} produktů")
        
        print("="*60)


# Pomocné funkce pro testování a ladění
def test_category_mapper():
    """Testovací funkce pro ověření funkčnosti mapperu."""
    mapper = CategoryMapper()
    
    # Testovací případy
    test_cases = [
        {
            "name": "Pánská mikina Nike Sportswear",
            "params": {"pohlavi": "pánské", "typ": "mikina", "znacka": "Nike"},
            "expected": "Muži > Pánské oblečení > Pánské mikiny"
        },
        {
            "name": "Dámské běžecké boty Adidas",
            "params": {"pohlavi": "dámské", "sport": "běh", "typ": "boty"},
            "expected": "Sporty > Běh > Běžecká obuv"
        },
        {
            "name": "Fotbalové kopačky Nike Mercurial FG",
            "params": {"sport": "fotbal", "typ": "kopačky", "povrch": "FG"},
            "expected": "Sporty > Fotbal > Kopačky > Lisovky"
        },
        {
            "name": "Dětský batoh na výlety",
            "params": {"pohlavi": "dětské", "typ": "batoh"},
            "expected": "Děti > Dětské doplňky > Dětské batohy"
        }
    ]
    
    print("Testování Category Mapperu:")
    print("-" * 60)
    
    for test in test_cases:
        category, mapping_type = mapper.map_product_to_category(
            test["name"],
            test["params"]
        )
        
        print(f"\nProdukt: {test['name']}")
        print(f"Parametry: {test['params']}")
        print(f"Očekáváno: {test['expected']}")
        print(f"Výsledek: {category} (typ: {mapping_type})")
        print(f"Status: {'✓ OK' if category == test['expected'] else '✗ CHYBA'}")
    
    mapper.print_mapping_report()


if __name__ == "__main__":
    # Spustit testy při přímém spuštění souboru
    test_category_mapper()