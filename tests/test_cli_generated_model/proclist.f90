!  This file was generated by kMOS (kMC modelling on steroids)
!  written by Max J. Hoffmann mjhoffmann@gmail.com (C) 2009-2012.
!  The model was written by Max J. Hoffmann.

!  This file is part of kmos.
!
!  kmos is free software; you can redistribute it and/or modify
!  it under the terms of the GNU General Public License as published by
!  the Free Software Foundation; either version 2 of the License, or
!  (at your option) any later version.
!
!  kmos is distributed in the hope that it will be useful,
!  but WITHOUT ANY WARRANTY; without even the implied warranty of
!  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
!  GNU General Public License for more details.
!
!  You should have received a copy of the GNU General Public License
!  along with kmos; if not, write to the Free Software
!  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
!  USA
!****h* kmos/proclist
! FUNCTION
!    Implements the kMC process list.
!
!******


module proclist
use kind_values
use base, only: &
    update_accum_rate, &
    determine_procsite, &
    update_clocks, &
    increment_procstat

use lattice, only: &
    default, &
    default_cus, &
    allocate_system, &
    nr2lattice, &
    lattice2nr, &
    add_proc, &
    can_do, &
    set_rate_const, &
    replace_species, &
    del_proc, &
    reset_site, &
    system_size, &
    spuck, &
    null_species, &
    get_species


implicit none



 ! Species constants



integer(kind=iint), parameter, public :: nr_of_species = 3
integer(kind=iint), parameter, public :: CO = 0
integer(kind=iint), parameter, public :: empty = 1
integer(kind=iint), parameter, public :: oxygen = 2
integer(kind=iint), public :: default_species = empty
integer(kind=iint), parameter, public :: representation_length = 0
integer(kind=iint), public :: seed_size = 12
integer(kind=iint), public :: seed ! random seed
integer(kind=iint), public, dimension(:), allocatable :: seed_arr ! random seed


! Process constants

integer(kind=iint), parameter, public :: CO_adsorption = 1
integer(kind=iint), parameter, public :: CO_desorption = 2


integer(kind=iint), parameter, public :: nr_of_proc = 2
character(len=2000), dimension(2) :: processes, rates

contains

subroutine do_kmc_step()

!****f* proclist/do_kmc_step
! FUNCTION
!    Performs exactly one kMC step.
!
! ARGUMENTS
!
!    ``none``
!******
    real(kind=rsingle) :: ran_proc, ran_time, ran_site
    integer(kind=iint) :: nr_site, proc_nr

    call random_number(ran_time)
    call random_number(ran_proc)
    call random_number(ran_site)
    call update_accum_rate
    call determine_procsite(ran_proc, ran_time, proc_nr, nr_site)
    call run_proc_nr(proc_nr, nr_site)
    call update_clocks(ran_time)

end subroutine do_kmc_step

subroutine get_kmc_step(proc_nr, nr_site)

!****f* proclist/get_kmc_step
! FUNCTION
!    Determines next step without executing it.
!
! ARGUMENTS
!
!    ``none``
!******
    real(kind=rsingle) :: ran_proc, ran_time, ran_site
    integer(kind=iint), intent(out) :: nr_site, proc_nr

    call random_number(ran_time)
    call random_number(ran_proc)
    call random_number(ran_site)
    call update_accum_rate
    call determine_procsite(ran_proc, ran_time, proc_nr, nr_site)
end subroutine get_kmc_step

subroutine get_occupation(occupation)

!****f* proclist/get_occupation
! FUNCTION
!    Evaluate current lattice configuration and returns
!    the normalized occupation as matrix. Different species
!    run along the first axis and different sites run
!    along the second.
!
! ARGUMENTS
!
!    ``none``
!******
    ! nr_of_species = 3, spuck = 1
    real(kind=rdouble), dimension(0:2, 1:1), intent(out) :: occupation

    integer(kind=iint) :: i, j, k, nr, species

    occupation = 0

    do k = 0, system_size(3)-1
        do j = 0, system_size(2)-1
            do i = 0, system_size(1)-1
                do nr = 1, spuck
                    ! shift position by 1, so it can be accessed
                    ! more straightforwardly from f2py interface
                    species = get_species((/i,j,k,nr/))
                    if(species.gt.null_species) then
                    occupation(species, nr) = &
                        occupation(species, nr) + 1
                    endif
                end do
            end do
        end do
    end do

    occupation = occupation/real(system_size(1)*system_size(2)*system_size(3))
end subroutine get_occupation

subroutine init(input_system_size, system_name, layer, no_banner)

!****f* proclist/init
! FUNCTION
!     Allocates the system and initializes all sites in the given
!     layer.
!
! ARGUMENTS
!
!    * ``input_system_size`` number of unit cell per axis.
!    * ``system_name`` identifier for reload file.
!    * ``layer`` initial layer.
!    * ``no_banner`` [optional] if True no copyright is issued.
!******
    integer(kind=iint), intent(in) :: layer
    integer(kind=iint), dimension(2), intent(in) :: input_system_size

    character(len=400), intent(in) :: system_name

    logical, optional, intent(in) :: no_banner

    if (.not. no_banner) then
        print *, "+------------------------------------------------------------+"
        print *, "|                                                            |"
        print *, "| This kMC Model 'test_cli_generated_model' was written by   |"
        print *, "|                                                            |"
        print *, "|           Max J. Hoffmann (mjhoffmann@gmail.com)           |"
        print *, "|                                                            |"
        print *, "| and implemented with the help of kmos,                     |"
        print *, "| which is distributed under GNU/GPL Version 3               |"
        print *, "| (C) Max J. Hoffmann mjhoffmann@gmail.com                   |"
        print *, "|                                                            |"
        print *, "| kmos is distributed in the hope that it will be useful     |"
        print *, "| but WIHTOUT ANY WARRANTY; without even the implied         |"
        print *, "| waranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR     |"
        print *, "| PURPOSE. See the GNU General Public License for more       |"
        print *, "| details.                                                   |"
        print *, "|                                                            |"
        print *, "| I appreciate, but do not require, attribution.             |"
        print *, "| An attribution usually includes the program name           |"
        print *, "| author, and URL. For example:                              |"
        print *, "| kmos by Max J. Hoffmann, (http://mhoffman.github.com/kmos) |"
        print *, "|                                                            |"
        print *, "+------------------------------------------------------------+"
        print *, ""
        print *, ""
    endif
    call allocate_system(nr_of_proc, input_system_size, system_name)
    call initialize_state(layer)
end subroutine init

subroutine initialize_state(layer)

!****f* proclist/initialize_state
! FUNCTION
!    Initialize all sites and book-keeping array
!    for the given layer.
!
! ARGUMENTS
!
!    * ``layer`` integer representing layer
!******
    integer(kind=iint), intent(in) :: layer

    integer(kind=iint) :: i, j, k, nr
    ! initialize random number generator
    allocate(seed_arr(seed_size))
    seed_arr = seed
    call random_seed(seed_size)
    call random_seed(put=seed_arr)
    deallocate(seed_arr)
    do k = 0, system_size(3)-1
        do j = 0, system_size(2)-1
            do i = 0, system_size(1)-1
                do nr = 1, spuck
                    call reset_site((/i, j, k, nr/), null_species)
                end do
                select case(layer)
                case (default)
                    call replace_species((/i, j, k, default_cus/), null_species, default_species)
                end select
            end do
        end do
    end do

    do k = 0, system_size(3)-1
        do j = 0, system_size(2)-1
            do i = 0, system_size(1)-1
                select case(layer)
                case(default)
                    call touchup_default_cus((/i, j, k, default_cus/))
                end select
            end do
        end do
    end do


end subroutine initialize_state

subroutine run_proc_nr(proc, nr_site)

!****f* proclist/run_proc_nr
! FUNCTION
!    Runs process ``proc`` on site ``nr_site``.
!
! ARGUMENTS
!
!    * ``proc`` integer representing the process number
!    * ``nr_site``  integer representing the site
!******
    integer(kind=iint), intent(in) :: proc
    integer(kind=iint), intent(in) :: nr_site

    integer(kind=iint), dimension(4) :: lsite

    call increment_procstat(proc)

    ! lsite = lattice_site, (vs. scalar site)
    lsite = nr2lattice(nr_site, :)

    select case(proc)
    case(CO_adsorption)
        call put_CO_default_cus(lsite)

    case(CO_desorption)
        call take_CO_default_cus(lsite)

    end select

end subroutine run_proc_nr

subroutine put_oxygen_default_cus(site)

    integer(kind=iint), dimension(4), intent(in) :: site

    ! update lattice
    call replace_species(site, empty, oxygen)

    ! disable affected processes
    if(can_do(CO_adsorption, site))then
        call del_proc(CO_adsorption, site)
    endif


end subroutine put_oxygen_default_cus

subroutine take_oxygen_default_cus(site)

    integer(kind=iint), dimension(4), intent(in) :: site

    ! update lattice
    call replace_species(site, oxygen, empty)

    ! enable affected processes
    call add_proc(CO_adsorption, site)

end subroutine take_oxygen_default_cus

subroutine put_CO_default_cus(site)

    integer(kind=iint), dimension(4), intent(in) :: site

    ! update lattice
    call replace_species(site, empty, CO)

    ! disable affected processes
    if(can_do(CO_adsorption, site))then
        call del_proc(CO_adsorption, site)
    endif

    ! enable affected processes
    call add_proc(CO_desorption, site)

end subroutine put_CO_default_cus

subroutine take_CO_default_cus(site)

    integer(kind=iint), dimension(4), intent(in) :: site

    ! update lattice
    call replace_species(site, CO, empty)

    ! disable affected processes
    if(can_do(CO_desorption, site))then
        call del_proc(CO_desorption, site)
    endif

    ! enable affected processes
    call add_proc(CO_adsorption, site)

end subroutine take_CO_default_cus

subroutine touchup_default_cus(site)

    integer(kind=iint), dimension(4), intent(in) :: site

    if (can_do(CO_adsorption, site)) then
        call del_proc(CO_adsorption, site)
    endif
    if (can_do(CO_desorption, site)) then
        call del_proc(CO_desorption, site)
    endif
    select case(get_species(site))
    case(CO)
        call add_proc(CO_desorption, site)
    case(empty)
        call add_proc(CO_adsorption, site)
    end select

end subroutine touchup_default_cus

end module proclist
