create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text not null default '',
    email text,
    created_at timestamptz not null default now()
);

alter table public.profiles
    add column if not exists full_name text not null default '';

alter table public.profiles
    add column if not exists email text;

alter table public.profiles enable row level security;

grant select, update on public.profiles to authenticated;

drop policy if exists "Users can view their own profile"
    on public.profiles;

create policy "Users can view their own profile"
    on public.profiles
    for select
    to authenticated
    using ((select auth.uid()) = id);

drop policy if exists "Users can update their own profile"
    on public.profiles;

create policy "Users can update their own profile"
    on public.profiles
    for update
    to authenticated
    using ((select auth.uid()) = id)
    with check ((select auth.uid()) = id);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (id, full_name, email)
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'full_name', ''),
        new.email
    )
    on conflict (id) do update
    set
        full_name = excluded.full_name,
        email = excluded.email;

    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
    after insert on auth.users
    for each row
    execute procedure public.handle_new_user();
