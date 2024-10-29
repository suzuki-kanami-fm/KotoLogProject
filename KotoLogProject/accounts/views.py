from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from accounts.forms import SignupForm, LoginForm, UserEditForm, UserPageForm, ChildForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, Family, Child
from journals.models import ChildcareJournalAccessLog,ChildcareJournal,Favorite
from django.urls import reverse_lazy,reverse
import uuid,json
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch, Count, Case, When, Value, BooleanField,Max,OuterRef, Subquery,Q
from django.core.serializers.json import DjangoJSONEncoder

class SignupView(View):

    def get(self, request, uuid=None):
        # UUIDが渡されている場合の家族情報の取得
        family = None
        if uuid:
            families = Family.objects.all()
            
            # invitationsの中から該当するUUIDを探す
            for fam in families:
                for invitation in fam.invitations:
                    if invitation['uuid'] == str(uuid) and not invitation['used']:
                        family = fam
                        break
                    
            if not family:
                messages.error(request, 'この招待URLは無効です。')
                return redirect('home')

        form = SignupForm()
        return render(request, "accounts/signup.html", context={"form": form, "uuid": uuid})

    def post(self, request, uuid=None):
        form = SignupForm(request.POST)
        family = None

        if uuid:
            families = Family.objects.all()
            
            # invitationsの中から該当するUUIDを探す
            for fam in families:
                for invitation in fam.invitations:
                    if invitation['uuid'] == str(uuid) and not invitation['used']:
                        family = fam
                        break
                    
            if not family:
                messages.error(request, 'この招待URLは無効です。')
                return redirect('home')

        if form.is_valid():
            user = form.save(commit=False)

            # UUIDでの家族情報を関連付け
            if family:
                user.family = family
                family.use_invitation(uuid)

            user.save()
            login(request, user)
            messages.success(request, '新規登録が完了しました。')
            return redirect('home')

        return render(request, "accounts/signup.html", context={"form": form})
       
class LoginView(View):
    
    def get(self, request, uuid=None):
        if uuid:
            families = Family.objects.all()
            
            # invitationsの中から該当するUUIDを探す
            for fam in families:
                for invitation in fam.invitations:
                    if invitation['uuid'] == str(uuid) and not invitation['used']:
                        family = fam
                        break


            if not family:
                messages.error(request, 'この招待URLは無効です。新しい招待URLを発行してください。')
                return redirect('home')

            # 既に家族登録されているユーザーがログインしている場合
            if request.user.is_authenticated:
                if request.user.family:
                    messages.error(request, "既に家族に所属しています。")
                    return redirect('accounts:user_page')

                # 家族登録が未済のログイン済みユーザーを登録
                request.user.family = family
                request.user.save()
                family.use_invitation(uuid)
                messages.success(request, "家族登録が完了しました！")
                return redirect('accounts:user_page')

            # 未ログインユーザーにはメッセージを出してそのままログイン画面表示
            messages.info(request, "家族登録を行うためにログインしてください。")

        return render(request, "accounts/login.html", context={'uuid': uuid})

    def post(self, request, uuid=None):
        form = LoginForm(request.POST)
        
        if form.is_valid():
            user = form.user_cache
            login(request, user)

            # UUIDが存在する場合、家族情報にユーザーを追加
            if uuid:
                families = Family.objects.all()
                
                # invitationsの中から該当するUUIDを探す
                for fam in families:
                    for invitation in fam.invitations:
                        if invitation['uuid'] == str(uuid) and not invitation['used']:
                            family = fam
                            break
                
                if family and user.family is None:
                    user.family = family
                    user.save()
                    family.use_invitation(uuid)
                    messages.success(request, "家族登録が完了しました！")
                    return redirect('accounts:user_page')
                elif family:
                    messages.info(request, "既に家族登録されています。")

            return redirect("home")

        return render(request, "accounts/login.html", context={'form': form})

class LogoutView(LoginRequiredMixin, LogoutView):
     template_name = "common/home.html"

class UserEditView(LoginRequiredMixin, View):
    
    def get(self, request):
        user = request.user
        form = UserEditForm(instance=user)
        password_form = PasswordChangeForm(user=request.user)
        return render(request, 'accounts/user_edit.html', {
            'form': form, 
            'user':user,
            "password_form":password_form
        })

    def post(self, request):
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:user_page")
        return render(request, "accounts/user_edit.html", {"form": form})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_change_form'] = PasswordChangeForm(user=self.request.user)
        return context    

class UserPageView(LoginRequiredMixin, View):
    
    def get(self, request):
        user = request.user
        form = UserPageForm(instance=user)

        # 家族が存在する場合は家族情報と子ども情報を取得
        family, family_members, children = self.get_family_info(user)    

        # カレンダー表示用のクエリを発行
        if family:
            records_by_date = ChildcareJournal.objects.filter(
                Q(user__in=family_members) | Q(user=user)).values('published_on').order_by('published_on')
            records_by_date = [
                {
                    'date': record['published_on'].strftime('%Y-%m-%d')
                }
                for record in records_by_date
            ]
        else:
            records_by_date = []

        # 最近見た育児記録の最新のアクセス時間を持つレコードを取得
        latest_recent_journals = (
            ChildcareJournalAccessLog.objects
            .filter(user=user)
            .values('childcare_journal_id')  # 各育児記録ごとにグループ化
            .annotate(latest_accessed=Max('accessed_at'))  # 最新のアクセス時間を取得
        )

        # 最近見た育児記録のクエリセットを生成
        recent_journal_objects = (
            ChildcareJournal.objects
            .filter(id__in=Subquery(latest_recent_journals.values('childcare_journal_id')))  # 最新のアクセスがある育児記録を絞り込み
            .annotate(
                latest_accessed=Subquery(
                    latest_recent_journals.filter(
                        childcare_journal_id=OuterRef('id')
                    ).values('latest_accessed')[:1]  # その育児記録の最新のアクセス日時を取得
                ),
                is_favorite=Case(
                    When(favorite__user=user, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
            .order_by('-latest_accessed')  # 最新のアクセス時間順に並べ替え
            .select_related('child')[:10]  # 必要な関連データを一緒に取得
        )

                
        # ユーザが作成した育児記録を取得
        user_created_journals = ChildcareJournal.objects.filter(user=user).order_by('-published_on').annotate(
            is_favorite=Case(
                When(favorite__user=user, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).select_related('child')[:10]
        

        child_form = ChildForm()
        

        # コンテキストに家族情報、子ども情報、フォームを追加
        context = {
            'form': form,
            'user': user,
            'family': family,
            'family_members': family_members,
            'children': children,  
            'child_form': child_form,
            'recent_journal_objects': recent_journal_objects, 
            'user_created_journals': user_created_journals,
            'records_by_date': json.dumps(records_by_date, cls=DjangoJSONEncoder),
        }
        return render(request, "accounts/user_page.html", context)

    
    def post(self, request):
        form = UserPageForm(request.POST, instance=request.user)
        user = request.user
        
        # 子ども追加処理
        if 'add_child' in request.POST:
            child_form = ChildForm(request.POST)
            
            # ユーザーに紐づくFamilyがなければ作成
            if not user.family:
                family = Family.objects.create()
                user.family = family
                user.save()
                        
            if child_form.is_valid():
                child = child_form.save(commit=False)
                child.family = request.user.family
               
                try:
                    child.save()
                    messages.success(request, '子どもが追加されました。')
                    return redirect('accounts:user_page')
                except Exception as e:
                    child_form.add_error(None, 'エラーが発生しました。再度お試しください。')
                                        
            # 家族が存在する場合は家族情報と子ども情報を取得
            family, family_members, children = self.get_family_info(user)
                
            return render(request, 'accounts/user_page.html', {
                'form': form,
                'child_form': child_form,
                'children': children,
                'family': user.family,
            })

    # 家族情報と子ども情報の取得を行う
    def get_family_info(self, user):
        family = user.family

        if family:
            family_members = User.objects.filter(family=family).exclude(id=user.id)
            children = Child.objects.filter(family=family).order_by('birthday')
        else:
            family_members, children = [], []
        return family, family_members, children
    
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        return render(self.request,"accounts/password_change_done.html" )

class CustomPasswordChangeDoneView(LoginRequiredMixin,PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'
    
class InvitationUrlView(LoginRequiredMixin, View):
    
    @transaction.atomic
    def get(self, request):
        user = request.user
        family = user.family

        # 家族が存在しない場合、新しいFamilyを作成し、ユーザーを関連付ける
        if not family:
            family = Family.objects.create()
            user.family = family
            user.save()

        # 新しい招待URLを発行し、`login_with_invite`にリダイレクトするリンクを生成
        invitation = family.generate_invitation()
        invitation_url = request.build_absolute_uri(reverse('accounts:login_with_invite', kwargs={'uuid': invitation['uuid']}))

        return render(request, 'accounts/invitation_url.html', {'invitation_url': invitation_url})

class FamilyDeleteView(LoginRequiredMixin, View):

    def post(self, request):
        # 現在のユーザーが所属するfamilyを取得
        family = request.user.family

        # 同じfamilyを持つユーザーの数をカウント
        family_members_count = User.objects.filter(family=family).count()

        # 家族情報を削除できるのは、familyのユーザーが2人以上いる場合のみ
        if family_members_count > 1:
            # 現在のユーザーのfamilyキーをNullに更新
            request.user.family = None
            request.user.save()
            messages.success(request, '家族情報を削除しました。')
        else:
            messages.error(request, '1人しかいない場合、家族情報は削除できません。')

        return redirect('accounts:user_page')

class ChildDeleteView(LoginRequiredMixin, View):

    def post(self, request, child_id):
        # 子ども情報を削除
        child = get_object_or_404(Child, id=child_id, family=request.user.family)

        try:
            child.delete()
            messages.success(request, '子ども情報が削除されました。')
        except Exception as e:
            messages.error(request, '子ども情報の削除に失敗しました。')

        return redirect('accounts:user_page')     