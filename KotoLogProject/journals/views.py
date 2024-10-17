from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from .forms import ChildcareJournalForm
from .models import (
    ChildcareJournal, Hashtag, 
    ChildcareJournalHashtag, Favorite,
    ChildcareJournalAccessLog)
from accounts.models import User,Child
from django.db.models import Prefetch, Count, Case, When, Value, BooleanField
from django.utils import timezone
from django.contrib import messages
import re

## 共通関数 ##

# 上位n件を取得
def get_top_n(queryset, n=10):
    return queryset[:n]

# お気に入りフラグを取得
def get_favorite_flagged_queryset(queryset, user):
    return queryset.annotate(
        is_favorite=Case(
            When(favorite__user=user, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).select_related('child')
    
class CreateChildcareJournalView(View):
    def get(self, request):
        # GETリクエストでフォームを表示
        form = ChildcareJournalForm()
        return render(request, 'journals/create_childcare_journal.html', {'form': form})

    def post(self, request):
        # POSTリクエストでフォームを送信
        form = ChildcareJournalForm(request.POST, request.FILES)
        
        if form.is_valid():
            # フォームから育児記録を保存
            childcare_journal = form.save(commit=False)
            childcare_journal.user = request.user  # 現在のユーザーを設定
            childcare_journal.save()
            
            # 本文からハッシュタグを抽出
            content = form.cleaned_data['content']
            hashtags = re.findall(r'#(\w+)', content)
            
            for hashtag_word in hashtags:
                # ハッシュタグをデータベースに保存（存在しない場合は新規作成）
                hashtag, created = Hashtag.objects.get_or_create(hashtag_word=hashtag_word)
                
                # ChildcareJournalHashtagモデルに関連付け
                ChildcareJournalHashtag.objects.get_or_create(
                    childcare_journal=childcare_journal,
                    hashtag=hashtag
                )
            
            # ホームページにリダイレクト
            return redirect('home')
        
        # バリデーションエラーが発生した場合は再度フォームを表示
        return render(request, 'journals/create_childcare_journal.html', {'form': form})

class EditChildcareJournalView(View):
    def get(self, request, journal_id):
        journal = get_object_or_404(ChildcareJournal, id=journal_id)
        form = ChildcareJournalForm(instance=journal)
        return render(request, 'journals/edit_childcare_journal.html', {'form': form, 'journal': journal})

    def post(self, request, journal_id):
        journal = get_object_or_404(ChildcareJournal, id=journal_id)
        form = ChildcareJournalForm(request.POST, request.FILES, instance=journal)

        if form.is_valid():
            form.save()
            messages.success(request, "育児記録が更新されました。")
            return redirect('home')

        return render(request, 'journals/edit_childcare_journal.html', {'form': form, 'journal': journal})

class ChildcareJournalDetailView(View):
    
    def get(self, request, journal_id):  
        journal = get_object_or_404(ChildcareJournal, pk=journal_id)
        journal.impression_count += 1
        journal.save(update_fields=['impression_count']) 

        if request.user.is_authenticated:
            access_log = ChildcareJournalAccessLog(
                user=request.user,
                childcare_journal=journal,
                accessed_at=timezone.now()
            )
            access_log.save()
            
        data = {
            'title': journal.title,
            'content': journal.content,
            'published_on': journal.published_on.strftime('%Y-%m-%d'),
            'is_public': journal.is_public,
            'image_url': journal.image_url.url if journal.image_url else None,
            'is_owner': journal.user == request.user,
            'is_favorited': Favorite.objects.filter(user=request.user, childcare_journal=journal).exists(),
        }
        return JsonResponse(data)

    def post(self, request, journal_id):
        journal = get_object_or_404(ChildcareJournal, id=journal_id)

        if 'add_to_favorites' in request.POST:
            if not Favorite.objects.filter(user=request.user, childcare_journal=journal).exists():
                Favorite.objects.create(user=request.user, childcare_journal=journal)
                return JsonResponse({'success': True, 'message': "育児記録をお気に入りに登録しました。", 'is_favorited': True})
            else:
                return JsonResponse({'success': False, 'message': "すでにお気に入りに登録されています。"})
        
        if 'remove_from_favorites' in request.POST:
            Favorite.objects.filter(user=request.user, childcare_journal=journal).delete()
            return JsonResponse({'success': True, 'message': "お気に入りを解除しました。", 'is_favorited': False})
        
        return JsonResponse({'success': False, 'message': "処理に失敗しました。"})
    
class HomeView(View):
    def get(self, request):
        
        # 公開されている育児記録
        public_journals = get_top_n(ChildcareJournal.objects.filter(is_public=True).select_related('user'))

        if request.user.is_authenticated:
            family_users = User.objects.filter(family=request.user.family)
            children = Child.objects.filter(family=request.user.family)

            # 各セグメントのデータ取得
            # 家族の育児記録
            family_journals = get_favorite_flagged_queryset(
                get_top_n(ChildcareJournal.objects.filter(user__in=family_users).select_related('user')),
                request.user
            )

            # 閲覧回数の多い育児記録
            popular_journals = get_favorite_flagged_queryset(
                get_top_n(ChildcareJournal.objects.annotate(count=Count('impression_count')).select_related('user')),
                request.user
            )

            # 各子どもの育児記録
            child_journals_dict = {}
            for child in children:
                child_journals = get_favorite_flagged_queryset(
                    ChildcareJournal.objects.filter(child=child).select_related('user'),
                    request.user
                )
                child_journals_dict[child.id] = get_top_n(child_journals)

            # お気に入りの育児記録
            favorite_journals = get_favorite_flagged_queryset(
                get_top_n(ChildcareJournal.objects.filter(favorite__user=request.user).select_related('user')),
                request.user
            )

            context = {
                'family_journals': family_journals,
                'public_journals': public_journals,
                'popular_journals': popular_journals,
                'child_journals': child_journals_dict,
                'favorite_journals': favorite_journals,
            }
        else:
            #　閲覧回数の多い育児記録(公開されているもののみ)
            popular_journals = get_top_n(ChildcareJournal.objects.filter(is_public=True).annotate(count=Count('impression_count')).order_by('-count').select_related('user'))

            context = {
                'popular_journals': popular_journals,
                'public_journals': public_journals,
            }

        return render(request, 'common/home.html', context)


class ChildcareJournalListView(View):
    def get(self, request):
        # GETリクエストで育児記録一覧を表示
        filter_type = request.GET.get('filter', 'recent')  # デフォルトは最近の記録
        search_query = request.GET.get('search', '')

        # フィルタリング
        if filter_type == 'family':
            records = ChildcareJournal.objects.filter(user__families=request.user.family).order_by('-updated_at')
        elif search_query:
            records = ChildcareJournal.objects.filter(content__icontains=search_query).order_by('-updated_at')
        else:
            records = ChildcareJournal.objects.order_by('-updated_at')

        context = {
            'records': records,
            'search_query': search_query,
            'filter_type': filter_type,
        }
        return render(request, 'journals/childcare_journal_list.html', context)

    def post(self, request):
        # POSTリクエストでフィルタリングまたは検索を処理
        search_query = request.POST.get('search', '')
        filter_type = request.POST.get('filter', 'recent')

        # フィルタリング処理
        if filter_type == 'family':
            records = ChildcareJournal.objects.filter(user__families=request.user.family).order_by('-updated_at')
        elif search_query:
            records = ChildcareJournal.objects.filter(content__icontains=search_query).order_by('-updated_at')
        else:
            records = ChildcareJournal.objects.order_by('-updated_at')

        context = {
            'records': records,
            'search_query': search_query,
            'filter_type': filter_type,
        }
        return render(request, 'journals/childcare_journal_list.html', context)
