INDEX_MAPPINGS = {
    "rpt_qt": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_half": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_biz": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_sec_eq": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_ad": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_ad_con":{
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_other": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
}