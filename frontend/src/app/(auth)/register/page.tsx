"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { differenceInYears, parseISO } from "date-fns";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Shield, Eye, EyeOff, CheckCircle, XCircle } from "lucide-react";
import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/lib/auth-store";

const schema = z.object({
  email: z.string().email("Email invalide"),
  pseudo: z.string().min(3, "Minimum 3 caractères").max(50).regex(/^[a-zA-Z0-9_\-]+$/, "Lettres, chiffres, _ et - uniquement"),
  password: z.string()
    .min(8, "Minimum 8 caractères")
    .regex(/[A-Z]/, "Au moins une majuscule")
    .regex(/[0-9]/, "Au moins un chiffre")
    .regex(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/, "Au moins un caractère spécial"),
  password_confirm: z.string(),
  birth_date: z.string().min(1, "Date de naissance requise"),
  accept_terms: z.literal(true, { errorMap: () => ({ message: "Vous devez accepter les CGU" }) }),
}).refine((d) => d.password === d.password_confirm, {
  message: "Les mots de passe ne correspondent pas",
  path: ["password_confirm"],
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [age, setAge] = useState<number | null>(null);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const birthDate = watch("birth_date");

  // Calcul âge en temps réel
  useEffect(() => {
    if (birthDate) {
      try {
        const calculated = differenceInYears(new Date(), parseISO(birthDate));
        setAge(isNaN(calculated) ? null : calculated);
      } catch {
        setAge(null);
      }
    } else {
      setAge(null);
    }
  }, [birthDate]);

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      const res = await authApi.register(data);
      const { access_token, pseudo, user_id, role, level, total_xp } = res.data;
      login(access_token, {
        id: user_id, pseudo, role, level, total_xp,
        email: data.email, is_verified_18: true,
        avatar_url: null, bio: null,
        created_at: new Date().toISOString(),
      });
      toast.success(`Bienvenue Agent ${pseudo} ! 🎮`);
      router.replace("/dashboard");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      const msg = error?.response?.data?.message || "Erreur lors de l'inscription";
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Shield className="text-cyber-green" size={48} />
          </div>
          <h1 className="text-3xl font-bold text-cyber-green glow-green">CYBERLEARN</h1>
          <p className="text-cyber-muted mt-2">Rejoindre la CSDF — Inscription 18+</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="cyber-card space-y-4">
          {/* Email */}
          <div>
            <label className="cyber-label">Adresse email</label>
            <input {...register("email")} type="email" placeholder="agent@csdf.gov"
              className="cyber-input" />
            {errors.email && <p className="cyber-error">{errors.email.message}</p>}
          </div>

          {/* Pseudo */}
          <div>
            <label className="cyber-label">Pseudo d'agent</label>
            <input {...register("pseudo")} type="text" placeholder="AlexChen_CSDF"
              className="cyber-input" />
            {errors.pseudo && <p className="cyber-error">{errors.pseudo.message}</p>}
          </div>

          {/* Mot de passe */}
          <div>
            <label className="cyber-label">Mot de passe</label>
            <div className="relative">
              <input {...register("password")} type={showPassword ? "text" : "password"}
                placeholder="••••••••" className="cyber-input pr-10" />
              <button type="button" onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-text">
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {errors.password && <p className="cyber-error">{errors.password.message}</p>}
          </div>

          {/* Confirmation */}
          <div>
            <label className="cyber-label">Confirmer le mot de passe</label>
            <input {...register("password_confirm")} type={showPassword ? "text" : "password"}
              placeholder="••••••••" className="cyber-input" />
            {errors.password_confirm && <p className="cyber-error">{errors.password_confirm.message}</p>}
          </div>

          {/* Date de naissance avec vérification âge temps réel */}
          <div>
            <label className="cyber-label">Date de naissance</label>
            <input {...register("birth_date")} type="date" className="cyber-input" />
            {/* Affichage âge calculé */}
            {age !== null && (
              <div className={`flex items-center gap-2 mt-2 text-sm ${age >= 18 ? "text-cyber-success" : "text-cyber-red"}`}>
                {age >= 18
                  ? <><CheckCircle size={16} /> {age} ans — Accès autorisé ✓</>
                  : <><XCircle size={16} /> {age} ans — Accès refusé (18+ requis) ✗</>
                }
              </div>
            )}
            {errors.birth_date && <p className="cyber-error">{errors.birth_date.message}</p>}
          </div>

          {/* CGU */}
          <div className="flex items-start gap-3">
            <input {...register("accept_terms")} type="checkbox" id="terms"
              className="mt-1 accent-cyber-green" />
            <label htmlFor="terms" className="text-sm text-cyber-muted">
              J'ai 18 ans ou plus et j'accepte les{" "}
              <span className="text-cyber-cyan cursor-pointer hover:underline">conditions d'utilisation</span>
              {" "}et la{" "}
              <span className="text-cyber-cyan cursor-pointer hover:underline">politique de confidentialité</span>.
            </label>
          </div>
          {errors.accept_terms && <p className="cyber-error">{errors.accept_terms.message}</p>}

          {/* Submit */}
          <button type="submit" disabled={isLoading || (age !== null && age < 18)}
            className="cyber-btn-primary w-full mt-2">
            {isLoading ? "Création du compte..." : "Rejoindre la CSDF →"}
          </button>

          <p className="text-center text-cyber-muted text-sm">
            Déjà un compte ?{" "}
            <Link href="/login" className="text-cyber-cyan hover:underline">Se connecter</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
