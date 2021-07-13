import datetime as dt
from posts.models import Profile

def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    year = dt.datetime.now().year

    return {'year': year}


def user_count(request):
    """
    Добавляет переменную с текущим годом.
    """
    counts = Profile.objects.count()

    return {'user_count': counts}
