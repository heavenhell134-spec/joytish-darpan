-- Supabase schema foundation. Apply only after creating a Supabase project.
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.birth_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  label text not null default 'My birth chart',
  birth_date date not null,
  birth_time time not null,
  timezone text not null,
  latitude double precision not null check (latitude between -90 and 90),
  longitude double precision not null check (longitude between -180 and 180),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.saved_charts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  birth_profile_id uuid not null references public.birth_profiles(id) on delete cascade,
  engine_version text not null,
  calculation_settings jsonb not null default '{}'::jsonb,
  chart_payload jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists birth_profiles_user_id_idx on public.birth_profiles(user_id);
create index if not exists saved_charts_user_id_created_at_idx on public.saved_charts(user_id, created_at desc);

alter table public.profiles enable row level security;
alter table public.birth_profiles enable row level security;
alter table public.saved_charts enable row level security;

create policy "Users can read their own profile" on public.profiles for select using (auth.uid() = id);
create policy "Users can insert their own profile" on public.profiles for insert with check (auth.uid() = id);
create policy "Users can update their own profile" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "Users can manage their own birth profiles" on public.birth_profiles
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users can manage their own saved charts" on public.saved_charts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
