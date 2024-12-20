from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from .forms import ChildcareJournalForm
from .models import (
    ChildcareJournal, Hashtag, 
    ChildcareJournalHashtag, Favorite,
    ChildcareJournalAccessLog)
from accounts.models import User,Child
from KotoLogProject.forms import SearchJournalForm
from django.db.models import Prefetch, Count, Case, When, Value, BooleanField,Q
from django.utils import timezone
from django.contrib import messages
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
import re
import hashlib
import subprocess
import os
import uuid

# アップロードファイルサイズ
MAX_FILE_SIZE_MB = 10  # 10MBに設定

## 共通関数 ##
# 上位n件を取得
def get_top_n(queryset, n=10):
    return queryset[:n]

# お気に入りフラグを取得
def get_favorite_flagged_queryset(queryset, user):
    return queryset.annotate(
        is_favorited=Case(
            When(favorite__user=user, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).select_related('child')

## 動画ファイルをMP4形式に変換する関数 ##
def convert_video_to_mp4(file_path):
    # 対象の拡張子を定義（webm, ogg, mov など）
    valid_video_extensions = ('.mov', '.webm', '.ogg')

    if file_path.lower().endswith(valid_video_extensions):
        try:
            # 出力ファイル名を変更してMP4にする（ユニークな名前を生成）
            base_name = os.path.splitext(file_path)[0]
            unique_mp4_file_path = f"{base_name}_{uuid.uuid4().hex}.mp4"
            
            # ffmpegを使用してMOVをMP4に変換
            command = f'ffmpeg -i "{file_path}" -vcodec h264 -acodec aac "{unique_mp4_file_path}"'
            subprocess.run(command, shell=True, check=True)
            
            # 変換後、元のMOVファイルを削除
            os.remove(file_path)
            
            return unique_mp4_file_path  # 成功した場合、新しいMP4ファイルのパスを返す
        except subprocess.CalledProcessError:
            return None  # 変換に失敗した場合
    return file_path  # MOV以外の形式はそのまま返す


class CreateChildcareJournalView(View):
    def get(self, request):
        children = Child.objects.filter(family=request.user.family)
        if not children.exists():
            messages.error(request, '育児記録の作成前に子ども情報を登録してください。')
            return redirect('accounts:user_page')
        
        form = ChildcareJournalForm(user=request.user)
        return render(request, 'journals/create_childcare_journal.html', {'form': form})

    def post(self, request):
        form = ChildcareJournalForm(request.POST, request.FILES)

        # ファイルチェック
        uploaded_file = request.FILES.get('image_url')
        if uploaded_file:
            if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                messages.error(request, f"ファイルサイズは{MAX_FILE_SIZE_MB}MB以下にしてください。")
                return render(request, 'journals/create_childcare_journal.html', {'form': form})
            
            # 許可するファイル拡張子（画像および動画ファイル形式）
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov','.webm', '.ogg']
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                messages.error(request, "対応しているファイル形式は .jpg, .jpeg, .png, .gif, .mp4, .mov, .webm, .ogg です。")
                return render(request, 'journals/create_childcare_journal.html', {'form': form})

            # ファイルの保存先を設定
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', uploaded_file.name)
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            # 動画ファイルの変換（MOVの場合）
            converted_file_path = convert_video_to_mp4(file_path)
            if converted_file_path is None:
                messages.error(request, "動画の変換に失敗しました。再度お試しください。")
                return render(request, 'journals/create_childcare_journal.html', {'form': form})

            # 変換後のファイルパスをフォームに渡す
            uploaded_file.name = os.path.basename(converted_file_path)

        if form.is_valid():
            # フォームから育児記録を保存
            childcare_journal = form.save(commit=False)
            childcare_journal.user = request.user # 現在のユーザーを設定
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
            delete_image_flag = request.POST.get("delete_image") == "1"
            new_image = request.FILES.get("image_url")
            
            #  削除フラグが立っている または 現在の画像と新しい画像が異なる場合に削除処理
            if delete_image_flag or (new_image and journal.image_url != new_image):
                if journal.image_url:
                    journal.image_url.delete()
                    journal.image_url = None
                    
            # 新しい画像の登録処理
            if new_image:
                journal.image_url = new_image
            
                # ファイルサイズチェック
                if new_image.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    messages.error(request, f"ファイルサイズは{MAX_FILE_SIZE_MB}MB以下にしてください。")
                    return render(request, 'journals/edit_childcare_journal.html', {'form': form, 'journal': journal})
                
                allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov','.webm', '.ogg']
                file_extension = new_image.name.split('.')[-1].lower()
                
                # ファイル形式チェック
                if file_extension not in allowed_extensions:
                    messages.error(request, "対応しているファイル形式は .jpg, .jpeg, .png, .gif, .mp4, .mov, .webm, .ogg です。")
                    return render(request, 'journals/edit_childcare_journal.html', {'form': form, 'journal': journal})

                # ファイルの保存先を設定
                file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', new_image.name)
                with open(file_path, 'wb') as f:
                    for chunk in new_image.chunks():
                        f.write(chunk)

                # 動画ファイルの変換（MOVの場合）
                converted_file_path = convert_video_to_mp4(file_path)
                if converted_file_path is None:
                    messages.error(request, "動画の変換に失敗しました。再度お試しください。")
                    return render(request, 'journals/edit_childcare_journal.html', {'form': form, 'journal': journal})

                # 変換後のファイルパスをフォームに渡す
                new_image.name = os.path.basename(converted_file_path)                

            # すべての処理が完了したら保存
            journal.save()
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
                'published_on': journal.published_on.strftime('%Y/%m/%d'),
                'is_public': journal.is_public,
                'image_url': journal.image_url.url if journal.image_url else None,
                'is_owner': journal.user == request.user,
                'is_favorited': Favorite.objects.filter(user=request.user, childcare_journal=journal).exists(),
            }
        else:
            data = {
                'title': journal.title,
                'content': journal.content,
                'published_on': journal.published_on.strftime('%Y/%m/%d'),
                'is_public': journal.is_public,
                'image_url': journal.image_url.url if journal.image_url else None,
                'is_owner': journal.user == request.user,
                'is_favorited': "",
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
                
        if request.user.is_authenticated:
            family_users = User.objects.filter(family=request.user.family)
            children = Child.objects.filter(family=request.user.family)

            # 各セグメントのデータ取得            
            
             # 公開されている育児記録
            public_journals = get_favorite_flagged_queryset(
                get_top_n(ChildcareJournal.objects.filter(is_public=True).select_related('user')),
                request.user
            )
            
            # 家族の育児記録
            family_journals = get_favorite_flagged_queryset(
                get_top_n(ChildcareJournal.objects.filter(user__in=family_users).select_related('user')),
                request.user
            )

            # 閲覧回数の多い育児記録
            popular_journals = get_favorite_flagged_queryset(
                get_top_n(
                    ChildcareJournal.objects.filter(
                        Q(is_public=True) | Q(user__in=family_users)
                    ).annotate(count=Count('impression_count')).select_related('user')
                ),
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
             # 公開されている育児記録
            public_journals = get_top_n(ChildcareJournal.objects.filter(is_public=True).select_related('user')) 
        
            #　閲覧回数の多い育児記録(公開されているもののみ)
            popular_journals = get_top_n(ChildcareJournal.objects.filter(is_public=True).annotate(count=Count('impression_count')).order_by('-count').select_related('user'))

            context = {
                'popular_journals': popular_journals,
                'public_journals': public_journals,
            }

        return render(request, 'common/home.html', context)


class ChildcareJournalListView(View):
    def get(self, request):
        user = request.user
        query_params = request.GET
        
        # 検索フォームをユーザー情報付きで生成
        search_form = SearchJournalForm(user=user, data=request.GET)

        # すべての育児記録を取得
        queryset = ChildcareJournal.objects.all()

        # 検索フォームの値セット
        search_query = query_params.get('search_query')
        segment = query_params.get('segment')
        child_id = query_params.get('child')
        filter_option = query_params.get('filter_option', '')

        # キーワード検索
        if search_query:
            
            # フィルター未選択の場合のデフォルト検索条件: 
            # ログインユーザー：公開されている育児記録 または 家族の育児記録
            # 未ログインユーザー：公開されている育児記録
            if request.user.is_authenticated:
                default_filter = Q(is_public=True) | Q(user__family=user.family)
            else:
                default_filter = Q(is_public=True)
    
            queryset = queryset.filter(
                default_filter,
                Q(title__icontains=search_query) | 
                Q(content__icontains=search_query) | 
                Q(childcarejournalhashtag__hashtag__hashtag_word__icontains=search_query)  # タグを含むフィルタリング
            ).distinct()

        # フィルタリング処理
        if segment == 'public' or filter_option == 'public':
            queryset = queryset.filter(is_public=True)
            
        elif (segment == 'family' or filter_option == 'family') and user.is_authenticated:

            queryset = queryset.filter(user__family=user.family)
        
        elif segment == 'child' or ('child' in filter_option):

            # 検索時はfilter_optionから抽出する
            if  filter_option:
                match = re.search(r'child_(\d+)', filter_option)  
                if match:
                    param_child_id = match.group(1)  # 抽出した ID
            
            # ホーム画面のセグメントを選択したときは、パラメータから子どもIDを取得する
            else:
                param_child_id = query_params.get("child_id")
            
            # 子どもIDに基づいてフィルタリング
            queryset = queryset.filter(child_id=param_child_id)
        
        elif filter_option == 'favorites' and user.is_authenticated:
            queryset = queryset.filter(favorite__user=user)

        # お気に入りのフィルタが指定されている場合
        if query_params.get('favorites') == 'true':
            queryset = queryset.filter(favorite__user=user)

        # 日付フィルターが指定されている場合
        filter_date = query_params.get('date')
        if filter_date:
            queryset = queryset.filter(published_on=filter_date)

        if request.user.is_authenticated:
            # 公開日付順に並べる
            queryset = get_favorite_flagged_queryset(queryset.order_by('-published_on'),user)
        else:
            queryset = queryset.order_by('-published_on')
       
        context = {
            'childcare_journals': queryset,
            'search_form': search_form,
        }
        
        return render(request, 'journals/childcare_journal_list.html', context)

class DeleteChildcareJournalsView(View):
    def post(self, request):
        selected_journal_ids = request.POST.getlist('selected_journals')
        journals_to_delete = ChildcareJournal.objects.filter(id__in=selected_journal_ids, user=request.user)

        if journals_to_delete.exists():
            journals_to_delete.delete()
            messages.success(request, '選択された育児記録が削除されました。')
        else:
            messages.error(request, '削除する記録が選択されていないか、削除権限がありません。')

        # 元のクエリパラメータを取得し、リダイレクトURLに追加
        query_params = request.GET.urlencode()
        redirect_url = reverse('journals:childcare_journal_list')
        if query_params:
            redirect_url += f'?{query_params}'

        return HttpResponseRedirect(redirect_url)