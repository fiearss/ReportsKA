from ReportOdt import KaForRssReport

data = {
    "path_template": 'two_table',
    "header": 'Отчет по системам мобильной космической связи',
    # "image_map": {
    #     "type": 'image',
    #     "blob": 'blob binary'
    # },
    "start": '01.01.2020',
    "end": '01.01.2020',
    "time": "01.01.2020 00:00:00",
    "RSS": [
        {
            "name": 'Якутск',
            "lat": 1,
            "lon": 1
        },
        {
            "name": 'СПБ52',
            "lat": 2,
            "lon": 2
        }
    ],
    "table": [
        {
            "test": '1'
        },
        {
            "test": '2'
        }
    ]
}


if __name__ == '__main__':
    report = KaForRssReport(data=data, template_name=data.get('path_template'))
    report.create_report()
    report.save_to_blob()